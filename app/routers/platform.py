import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.models.models import (
    Organisation,
    Subscription,
    SubscriptionStatus,
    TenantInvitation,
    User,
    UserRole,
)
from app.routers.deps import require_platform_owner
from app.schemas.schemas import (
    PlatformOrganisationCreate,
    PlatformOrganisationDetail,
    PlatformOrganisationPatch,
    PlatformOrganisationSummary,
    PlatformSubscriptionExpiringOut,
    UserOut,
)

router = APIRouter(prefix="/platform", tags=["platform"])


def _normalise_slug(value: str) -> str:
    return value.strip().lower().replace(" ", "-")


def _make_licence_number(slug: str) -> str:
    return f"TENANT-{slug[:32].upper()}"


def _make_token_and_hash() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return token, token_hash


@router.get("/organisations", response_model=list[PlatformOrganisationSummary])
def list_organisations(
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_owner),
):
    organisations = db.query(Organisation).order_by(Organisation.created_at.desc()).all()
    items: list[PlatformOrganisationSummary] = []
    for org in organisations:
        latest_subscription = (
            db.query(Subscription)
            .filter(Subscription.organisation_id == org.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )
        tenant_admin = (
            db.query(User)
            .filter(
                User.organisation_id == org.id,
                User.role.in_([UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN]),
            )
            .order_by(User.created_at.asc())
            .first()
        )
        items.append(
            PlatformOrganisationSummary(
                id=org.id,
                name=org.name,
                slug=org.slug,
                is_active=org.is_active,
                portal_plan=org.portal_plan,
                portal_expires_at=org.portal_expires_at,
                tenant_admin_email=tenant_admin.email if tenant_admin else None,
                subscription_status=latest_subscription.status.value if latest_subscription else None,
                subscription_current_period_end=latest_subscription.current_period_end if latest_subscription else None,
            )
        )
    return items


@router.get("/organisations/{organisation_id}", response_model=PlatformOrganisationDetail)
def get_organisation_detail(
    organisation_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_owner),
):
    organisation = db.query(Organisation).filter(Organisation.id == organisation_id).first()
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    admins = (
        db.query(User)
        .filter(
            User.organisation_id == organisation.id,
            User.role.in_([UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN, UserRole.HR_OFFICER]),
        )
        .order_by(User.created_at.asc())
        .all()
    )
    latest_subscription = (
        db.query(Subscription)
        .filter(Subscription.organisation_id == organisation.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )

    latest_subscription_out = None
    if latest_subscription:
        latest_subscription_out = {
            "id": latest_subscription.id,
            "status": latest_subscription.status.value,
            "plan_code": latest_subscription.plan_code,
            "billing_interval": latest_subscription.billing_interval,
            "amount": latest_subscription.amount,
            "currency": latest_subscription.currency,
            "current_period_start": latest_subscription.current_period_start,
            "current_period_end": latest_subscription.current_period_end,
            "cancel_at_period_end": latest_subscription.cancel_at_period_end,
        }

    return PlatformOrganisationDetail(
        id=organisation.id,
        name=organisation.name,
        licence_number=organisation.licence_number,
        slug=organisation.slug,
        is_active=organisation.is_active,
        portal_plan=organisation.portal_plan,
        portal_expires_at=organisation.portal_expires_at,
        admin_users=[UserOut.model_validate(admin) for admin in admins],
        latest_subscription=latest_subscription_out,
    )


@router.post("/organisations", response_model=PlatformOrganisationDetail, status_code=status.HTTP_201_CREATED)
def create_organisation(
    payload: PlatformOrganisationCreate,
    db: Session = Depends(get_db),
    creator: User = Depends(require_platform_owner),
):
    slug = _normalise_slug(payload.slug)
    if not slug:
        raise HTTPException(status_code=400, detail="slug is required")

    existing_slug = db.query(Organisation).filter(Organisation.slug == slug).first()
    if existing_slug:
        raise HTTPException(status_code=400, detail="slug already exists")

    existing_admin = db.query(User).filter(User.email == payload.admin_email).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="admin email already exists")

    organisation = Organisation(
        name=payload.name.strip(),
        slug=slug,
        licence_number=_make_licence_number(slug),
        portal_plan=payload.plan_code,
        portal_expires_at=payload.portal_expires_at,
        is_active=True,
    )
    db.add(organisation)
    db.flush()

    admin_user = User(
        email=payload.admin_email.strip().lower(),
        hashed_password=hash_password(payload.admin_password),
        full_name=payload.admin_name.strip(),
        role=UserRole.TENANT_ADMIN,
        organisation_id=organisation.id,
        must_reset_password=True,
    )
    db.add(admin_user)

    now = datetime.now(timezone.utc)
    subscription = Subscription(
        organisation_id=organisation.id,
        provider="manual",
        plan_code=payload.plan_code,
        status=SubscriptionStatus.ACTIVE,
        billing_interval="month",
        amount=0,
        currency="GBP",
        current_period_start=now,
        current_period_end=payload.portal_expires_at,
    )
    db.add(subscription)
    db.flush()

    token, token_hash = _make_token_and_hash()
    invitation = TenantInvitation(
        organisation_id=organisation.id,
        email=admin_user.email,
        role=UserRole.TENANT_ADMIN,
        token_hash=token_hash,
        expires_at=now + timedelta(days=7),
        created_by_user_id=creator.id,
    )
    db.add(invitation)
    db.commit()

    return PlatformOrganisationDetail(
        id=organisation.id,
        name=organisation.name,
        licence_number=organisation.licence_number,
        slug=organisation.slug,
        is_active=organisation.is_active,
        portal_plan=organisation.portal_plan,
        portal_expires_at=organisation.portal_expires_at,
        admin_users=[UserOut.model_validate(admin_user)],
        latest_subscription={
            "id": subscription.id,
            "status": subscription.status.value,
            "plan_code": subscription.plan_code,
            "billing_interval": subscription.billing_interval,
            "amount": subscription.amount,
            "currency": subscription.currency,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "invite_token_preview": token[:10],
        },
    )


@router.patch("/organisations/{organisation_id}", response_model=PlatformOrganisationDetail)
def patch_organisation(
    organisation_id: str,
    payload: PlatformOrganisationPatch,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_owner),
):
    organisation = db.query(Organisation).filter(Organisation.id == organisation_id).first()
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    updates = payload.model_dump(exclude_unset=True)
    if "slug" in updates and updates["slug"] is not None:
        updates["slug"] = _normalise_slug(updates["slug"])
        dupe = (
            db.query(Organisation)
            .filter(Organisation.slug == updates["slug"], Organisation.id != organisation_id)
            .first()
        )
        if dupe:
            raise HTTPException(status_code=400, detail="slug already exists")

    for key, value in updates.items():
        setattr(organisation, key, value)

    db.commit()
    db.refresh(organisation)

    admins = (
        db.query(User)
        .filter(
            User.organisation_id == organisation.id,
            User.role.in_([UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN, UserRole.HR_OFFICER]),
        )
        .order_by(User.created_at.asc())
        .all()
    )
    latest_subscription = (
        db.query(Subscription)
        .filter(Subscription.organisation_id == organisation.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )

    return PlatformOrganisationDetail(
        id=organisation.id,
        name=organisation.name,
        licence_number=organisation.licence_number,
        slug=organisation.slug,
        is_active=organisation.is_active,
        portal_plan=organisation.portal_plan,
        portal_expires_at=organisation.portal_expires_at,
        admin_users=[UserOut.model_validate(admin) for admin in admins],
        latest_subscription=(
            {
                "id": latest_subscription.id,
                "status": latest_subscription.status.value,
                "plan_code": latest_subscription.plan_code,
                "billing_interval": latest_subscription.billing_interval,
                "amount": latest_subscription.amount,
                "currency": latest_subscription.currency,
                "current_period_start": latest_subscription.current_period_start,
                "current_period_end": latest_subscription.current_period_end,
                "cancel_at_period_end": latest_subscription.cancel_at_period_end,
            }
            if latest_subscription
            else None
        ),
    )


@router.get("/subscriptions/expiring", response_model=list[PlatformSubscriptionExpiringOut])
def list_expiring_subscriptions(
    days: int = Query(default=30, ge=1, le=365),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_owner),
):
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=days)
    status_enum: SubscriptionStatus | None = None
    if status_filter:
        try:
            status_enum = SubscriptionStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid status filter") from exc

    query = (
        db.query(Subscription, Organisation)
        .join(Organisation, Organisation.id == Subscription.organisation_id)
        .filter(Subscription.current_period_end.is_not(None))
        .filter(Subscription.current_period_end <= window_end)
    )
    if status_enum:
        query = query.filter(Subscription.status == status_enum)

    rows = query.order_by(Subscription.current_period_end.asc()).all()
    return [
        PlatformSubscriptionExpiringOut(
            organisation_id=organisation.id,
            organisation_name=organisation.name,
            organisation_slug=organisation.slug,
            subscription_id=subscription.id,
            status=subscription.status.value,
            plan_code=subscription.plan_code,
            current_period_end=subscription.current_period_end,
        )
        for subscription, organisation in rows
    ]


@router.post("/organisations/{organisation_id}/resend-invite")
def resend_invite(
    organisation_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_platform_owner),
):
    organisation = db.query(Organisation).filter(Organisation.id == organisation_id).first()
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    admin = (
        db.query(User)
        .filter(User.organisation_id == organisation.id, User.role == UserRole.TENANT_ADMIN)
        .order_by(User.created_at.asc())
        .first()
    )
    if not admin:
        raise HTTPException(status_code=404, detail="Tenant admin not found")

    token, token_hash = _make_token_and_hash()
    invite = TenantInvitation(
        organisation_id=organisation.id,
        email=admin.email,
        role=UserRole.TENANT_ADMIN,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_by_user_id=actor.id,
    )
    db.add(invite)
    db.commit()

    return {
        "message": "Invitation token regenerated",
        "organisation_id": organisation.id,
        "email": admin.email,
        "invite_token_preview": token[:10],
    }
