import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_password
from app.models.models import (
    Organisation,
    Subscription,
    SubscriptionEvent,
    SubscriptionStatus,
    TenantInvitation,
    User,
    UserRole,
)
from app.schemas.schemas import (
    BillingWebhookRequest,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PortalBootstrapRequest,
    PublicPlanOut,
)

router = APIRouter(tags=["saas"])

settings = get_settings()

PLANS: dict[str, PublicPlanOut] = {
    "starter_monthly": PublicPlanOut(
        code="starter_monthly",
        name="Starter",
        amount=99,
        currency="GBP",
        billing_interval="month",
        features=["Up to 50 workers", "Core compliance dashboard", "Document tracking"],
    ),
    "growth_monthly": PublicPlanOut(
        code="growth_monthly",
        name="Growth",
        amount=249,
        currency="GBP",
        billing_interval="month",
        features=["Up to 250 workers", "Advanced reporting", "Risk and alerts"],
    ),
    "enterprise_monthly": PublicPlanOut(
        code="enterprise_monthly",
        name="Enterprise",
        amount=599,
        currency="GBP",
        billing_interval="month",
        features=["Unlimited workers", "Priority support", "Custom onboarding"],
    ),
}


def _slugify(value: str) -> str:
    slug = value.strip().lower().replace(" ", "-")
    return "".join(ch for ch in slug if ch.isalnum() or ch == "-")


def _status_to_org_active(status: str) -> bool:
    return status in {"active", "trialing"}


@router.get("/public/plans", response_model=list[PublicPlanOut])
def get_public_plans():
    return list(PLANS.values())


@router.post("/billing/checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(payload: CheckoutSessionRequest):
    plan = PLANS.get(payload.plan_code)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan_code")

    session_id = f"manual_{secrets.token_hex(10)}"
    base_url = settings.APP_BASE_URL or "http://127.0.0.1:3000"
    checkout_url = (
        f"{base_url}/checkout/success"
        f"?session_id={session_id}"
        f"&plan={plan.code}"
        f"&company={_slugify(payload.company_name)}"
    )
    return CheckoutSessionResponse(checkout_url=checkout_url, session_id=session_id)


@router.post("/billing/webhook")
def billing_webhook(
    payload: BillingWebhookRequest,
    db: Session = Depends(get_db),
    x_webhook_secret: str | None = Header(default=None),
):
    if settings.STRIPE_WEBHOOK_SECRET:
        if x_webhook_secret != settings.STRIPE_WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")

    existing = (
        db.query(SubscriptionEvent)
        .filter(SubscriptionEvent.provider_event_id == payload.provider_event_id)
        .first()
    )
    if existing:
        return {"status": "ok", "idempotent": True}

    slug = _slugify(payload.company_slug or payload.company_name)
    if not slug:
        raise HTTPException(status_code=400, detail="Invalid company slug")

    org = db.query(Organisation).filter(Organisation.slug == slug).first()
    if not org:
        org = Organisation(
            name=payload.company_name.strip(),
            slug=slug,
            licence_number=f"TENANT-{slug[:32].upper()}",
            portal_plan=payload.plan_code,
            is_active=_status_to_org_active(payload.status),
            portal_expires_at=payload.current_period_end,
        )
        db.add(org)
        db.flush()

    admin = db.query(User).filter(User.email == payload.admin_email.lower().strip()).first()
    if not admin:
        temp_password = secrets.token_urlsafe(12)
        admin = User(
            organisation_id=org.id,
            email=payload.admin_email.lower().strip(),
            full_name=payload.admin_name.strip(),
            role=UserRole.TENANT_ADMIN,
            hashed_password=hash_password(temp_password),
            must_reset_password=True,
            is_active=True,
        )
        db.add(admin)
        db.flush()

    subscription = None
    if payload.provider_subscription_id:
        subscription = (
            db.query(Subscription)
            .filter(Subscription.provider_subscription_id == payload.provider_subscription_id)
            .first()
        )
    if not subscription:
        subscription = (
            db.query(Subscription)
            .filter(Subscription.organisation_id == org.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )

    try:
        status_enum = SubscriptionStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid subscription status") from exc

    if not subscription:
        subscription = Subscription(
            organisation_id=org.id,
            provider=settings.PAYMENT_PROVIDER or "stripe",
            plan_code=payload.plan_code,
            status=status_enum,
            billing_interval=payload.billing_interval,
            amount=payload.amount,
            currency=payload.currency,
            provider_customer_id=payload.provider_customer_id,
            provider_subscription_id=payload.provider_subscription_id,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=payload.current_period_end,
        )
        db.add(subscription)
        db.flush()
    else:
        subscription.plan_code = payload.plan_code
        subscription.status = status_enum
        subscription.billing_interval = payload.billing_interval
        subscription.amount = payload.amount
        subscription.currency = payload.currency
        subscription.provider_customer_id = payload.provider_customer_id
        subscription.provider_subscription_id = payload.provider_subscription_id
        subscription.current_period_end = payload.current_period_end

    org.portal_plan = payload.plan_code
    org.portal_expires_at = payload.current_period_end
    org.is_active = _status_to_org_active(payload.status)

    event = SubscriptionEvent(
        subscription_id=subscription.id,
        provider_event_id=payload.provider_event_id,
        event_type=payload.event_type,
        payload_json=payload.model_dump(),
        status="processed",
        processed_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    return {"status": "ok", "idempotent": False, "organisation_id": org.id}


@router.post("/portal/bootstrap")
def portal_bootstrap(payload: PortalBootstrapRequest, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    invitation = (
        db.query(TenantInvitation)
        .filter(
            TenantInvitation.token_hash == token_hash,
            TenantInvitation.email == payload.email.lower().strip(),
        )
        .first()
    )
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.accepted_at is not None:
        raise HTTPException(status_code=400, detail="Invitation already used")
    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invitation expired")

    user = (
        db.query(User)
        .filter(
            User.organisation_id == invitation.organisation_id,
            User.email == invitation.email,
            User.role == UserRole.TENANT_ADMIN,
        )
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Tenant admin user not found")

    user.hashed_password = hash_password(payload.password)
    user.must_reset_password = False
    user.is_active = True
    if payload.full_name:
        user.full_name = payload.full_name.strip()

    invitation.accepted_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "ok", "message": "Portal bootstrap completed"}
