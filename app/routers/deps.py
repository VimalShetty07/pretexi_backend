from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import User, UserRole

security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if user.role == UserRole.INSPECTOR and user.access_expires_at:
        if user.access_expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inspector access has expired",
            )

    return user


def require_roles(*allowed_roles: UserRole):
    """Dependency factory — restrict access to specific roles."""
    def check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' does not have permission for this action",
            )
        return current_user
    return check


# Convenience shortcuts
require_admin = require_roles(UserRole.SUPER_ADMIN)
require_admin_or_manager = require_roles(UserRole.SUPER_ADMIN, UserRole.COMPLIANCE_MANAGER)
require_staff = require_roles(UserRole.SUPER_ADMIN, UserRole.COMPLIANCE_MANAGER, UserRole.HR_OFFICER, UserRole.PAYROLL_OFFICER)
require_any_admin = require_roles(UserRole.SUPER_ADMIN, UserRole.COMPLIANCE_MANAGER, UserRole.HR_OFFICER, UserRole.PAYROLL_OFFICER, UserRole.INSPECTOR)
