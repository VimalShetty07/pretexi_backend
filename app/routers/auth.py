from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.models import User, Organisation, UserRole, AuditLog, Worker
from app.schemas.schemas import (
    LoginRequest, RegisterRequest, TokenResponse, UserOut, UserCreate, UserUpdate,
)
from app.routers.deps import get_current_user, require_admin

router = APIRouter(prefix="/auth", tags=["auth"])


def _require_user_admin(user: User) -> None:
    if user.role not in (UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN):
        raise HTTPException(status_code=403, detail="Only tenant or super admins can manage users")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    org = Organisation(
        name=payload.organisation_name,
        licence_number=payload.licence_number,
    )
    db.add(org)
    db.flush()

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.SUPER_ADMIN,
        organisation_id=org.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "org": org.id, "role": user.role.value})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    identifier = payload.identifier.strip()

    user = db.query(User).filter(User.email == identifier).first()

    if not user:
        worker = db.query(Worker).filter(Worker.employee_id == identifier).first()
        if worker:
            user = db.query(User).filter(User.worker_id == worker.id).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid ID or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # Check inspector expiry
    if user.role == UserRole.INSPECTOR and user.access_expires_at:
        if user.access_expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=403, detail="Inspector access has expired")

    user.last_login = datetime.now(timezone.utc)
    db.add(AuditLog(
        user_id=user.id, user_email=user.email, user_role=user.role.value,
        action="LOGIN", entity_type="user", entity_id=user.id,
    ))
    db.commit()

    token = create_access_token({"sub": user.id, "org": user.organisation_id, "role": user.role.value})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ── User management (admin only) ──────────────────────────

@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    _require_user_admin(admin)
    query = db.query(User).filter(User.organisation_id == admin.organisation_id)
    if admin.role == UserRole.TENANT_ADMIN:
        query = query.filter(User.role == UserRole.HR_OFFICER)
    return query.all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    _require_user_admin(admin)
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    role_value = payload.role
    if admin.role == UserRole.TENANT_ADMIN:
        if payload.role != UserRole.HR_OFFICER.value:
            raise HTTPException(status_code=403, detail="Tenant admin can only create HR users")
        role_value = UserRole.HR_OFFICER.value

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=role_value,
        organisation_id=admin.organisation_id,
        worker_id=payload.worker_id,
        access_expires_at=payload.access_expires_at,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    _require_user_admin(admin)
    user = db.query(User).filter(User.id == user_id, User.organisation_id == admin.organisation_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if admin.role == UserRole.TENANT_ADMIN:
        if user.role != UserRole.HR_OFFICER:
            raise HTTPException(status_code=403, detail="Tenant admin can only update HR users")
        if payload.role and payload.role != UserRole.HR_OFFICER.value:
            raise HTTPException(status_code=403, detail="Tenant admin cannot change HR role")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user
