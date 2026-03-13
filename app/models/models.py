import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, Date,
    ForeignKey, Enum as SAEnum, JSON, LargeBinary,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    PLATFORM_OWNER = "platform_owner"
    TENANT_ADMIN = "tenant_admin"
    TENANT_STAFF = "tenant_staff"
    TENANT_EMPLOYEE = "tenant_employee"
    COMPLIANCE_MANAGER = "compliance_manager"
    HR_OFFICER = "hr_officer"
    PAYROLL_OFFICER = "payroll_officer"
    INSPECTOR = "inspector"              # read-only temporary access
    EMPLOYEE = "employee"                # worker portal access


class WorkerStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class WorkerStage(str, enum.Enum):
    RECRUITMENT = "recruitment"
    COS_ASSIGNMENT = "cos_assignment"
    PRE_START = "pre_start"
    ACTIVE_SPONSORSHIP = "active_sponsorship"
    TERMINATED = "terminated"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    MISSING = "missing"
    NEEDS_RESUBMISSION = "needs_resubmission"
    REJECTED = "rejected"


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, enum.Enum):
    VISA_EXPIRY = "visa_expiry"
    PASSPORT_EXPIRY = "passport_expiry"
    BRP_EXPIRY = "brp_expiry"
    MISSING_DOCUMENT = "missing_document"
    SALARY_RISK = "salary_risk"
    ABSENCE = "absence"
    REPORTING_DEADLINE = "reporting_deadline"
    REGISTRATION_EXPIRY = "registration_expiry"
    COS_ANOMALY = "cos_anomaly"
    WORKER_NOT_STARTED = "worker_not_started"
    VISA_REFUSED = "visa_refused"
    LOCATION_CHANGE = "location_change"
    FEE_RECOVERY_BREACH = "fee_recovery_breach"
    LICENCE_RISK = "licence_risk"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    SUBMITTED = "submitted"


class ReportDeadlineType(str, enum.Enum):
    TEN_WORKING_DAYS = "10_working_days"
    TWENTY_WORKING_DAYS = "20_working_days"


class LicenceRating(str, enum.Enum):
    A = "A"
    B = "B"


class RiskCategory(str, enum.Enum):
    COMPLIANT = "compliant"
    MINOR_BREACH = "minor_breach"          # B-rating risk
    SUSPENSION_RISK = "suspension_risk"
    REVOCATION_RISK = "revocation_risk"
    CIVIL_PENALTY = "civil_penalty"
    ILLEGAL_WORKER = "illegal_worker"


class ContactChangeStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class WorkerRequestStatus(str, enum.Enum):
    OPEN = "open"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class CosType(str, enum.Enum):
    DEFINED = "defined"
    UNDEFINED = "undefined"


class AbsenceType(str, enum.Enum):
    AUTHORISED = "authorised"
    UNAUTHORISED = "unauthorised"
    SICK = "sick"
    ANNUAL_LEAVE = "annual_leave"
    UNPAID = "unpaid"
    OTHER = "other"


class LeaveType(str, enum.Enum):
    ANNUAL = "annual"
    SICK = "sick"
    UNPAID = "unpaid"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    COMPASSIONATE = "compassionate"
    OTHER = "other"


class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class SubscriptionStatus(str, enum.Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


# ═══════════════════════════════════════════════════════════
#  ORGANISATION
# ═══════════════════════════════════════════════════════════

class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    licence_number: Mapped[str] = mapped_column(String(50), unique=True)
    slug: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    portal_plan: Mapped[str] = mapped_column(String(50), default="free")
    portal_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rating: Mapped[LicenceRating] = mapped_column(SAEnum(LicenceRating), default=LicenceRating.A)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    sector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    incorporation_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)

    # CoS allocation
    cos_allocated: Mapped[int] = mapped_column(Integer, default=0)
    cos_used: Mapped[int] = mapped_column(Integer, default=0)

    # Key personnel
    authorised_officer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    key_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Licence
    licence_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_sms_update: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Risk & health
    health_score: Mapped[int] = mapped_column(Integer, default=100)
    risk_category: Mapped[RiskCategory] = mapped_column(SAEnum(RiskCategory), default=RiskCategory.COMPLIANT)

    # Portal settings
    portal_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    portal_show_cos_ref: Mapped[bool] = mapped_column(Boolean, default=False)
    portal_show_salary: Mapped[bool] = mapped_column(Boolean, default=False)
    portal_require_edit_approval: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="organisation", cascade="all, delete-orphan")
    workers: Mapped[list["Worker"]] = relationship(back_populates="organisation", cascade="all, delete-orphan")
    key_personnel: Mapped[list["KeyPersonnel"]] = relationship(back_populates="organisation", cascade="all, delete-orphan")
    org_changes: Mapped[list["OrgChangeLog"]] = relationship(back_populates="organisation", cascade="all, delete-orphan")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="organisation", cascade="all, delete-orphan")
    tenant_invitations: Mapped[list["TenantInvitation"]] = relationship(back_populates="organisation", cascade="all, delete-orphan")


# ═══════════════════════════════════════════════════════════
#  KEY PERSONNEL (AO, Level 1, Level 2 users on SMS)
# ═══════════════════════════════════════════════════════════

class KeyPersonnel(Base):
    __tablename__ = "key_personnel"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organisation_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"))
    name: Mapped[str] = mapped_column(String(255))
    sms_role: Mapped[str] = mapped_column(String(50))  # authorising_officer, level_1, level_2
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    added_date: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    removed_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    organisation: Mapped["Organisation"] = relationship(back_populates="key_personnel")


# ═══════════════════════════════════════════════════════════
#  ORGANISATION CHANGE LOG (20 working day tracking)
# ═══════════════════════════════════════════════════════════

class OrgChangeLog(Base):
    __tablename__ = "org_change_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organisation_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"))
    change_type: Mapped[str] = mapped_column(String(255))  # merger, takeover, insolvency, address_change, etc.
    description: Mapped[str] = mapped_column(Text)
    reported_to_ho: Mapped[bool] = mapped_column(Boolean, default=False)
    report_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reported_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    organisation: Mapped["Organisation"] = relationship(back_populates="org_changes")


# ═══════════════════════════════════════════════════════════
#  USER (role-based: admin, hr, compliance, payroll, employee)
# ═══════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organisation_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.HR_OFFICER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # For EMPLOYEE role: linked to a specific worker record
    worker_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("workers.id"), nullable=True)

    # For INSPECTOR role: temporary access
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Security
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    must_reset_password: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    organisation: Mapped["Organisation"] = relationship(back_populates="users")
    worker: Mapped["Worker | None"] = relationship(back_populates="portal_user", foreign_keys=[worker_id])


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organisation_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), index=True)
    provider: Mapped[str] = mapped_column(String(32), default="stripe")
    provider_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan_code: Mapped[str] = mapped_column(String(100))
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, native_enum=False),
        default=SubscriptionStatus.ACTIVE,
    )
    billing_interval: Mapped[str] = mapped_column(String(20), default="month")
    amount: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="GBP")
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    organisation: Mapped["Organisation"] = relationship(back_populates="subscriptions")
    events: Mapped[list["SubscriptionEvent"]] = relationship(back_populates="subscription", cascade="all, delete-orphan")


class SubscriptionEvent(Base):
    __tablename__ = "subscription_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    subscription_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("subscriptions.id"), nullable=True)
    provider_event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="received")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    subscription: Mapped["Subscription | None"] = relationship(back_populates="events")


class TenantInvitation(Base):
    __tablename__ = "tenant_invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organisation_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False),
        default=UserRole.TENANT_ADMIN,
    )
    token_hash: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    organisation: Mapped["Organisation"] = relationship(back_populates="tenant_invitations")


# ═══════════════════════════════════════════════════════════
#  WORKER (the core entity — full lifecycle)
# ═══════════════════════════════════════════════════════════

class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organisation_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"))

    # ── Personal details ───────────────────────────────
    name: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    personal_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    place_of_birth: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country_of_birth: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ethnicity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    religion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ni_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    next_of_kin_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    next_of_kin_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Passport details ────────────────────────────────
    passport_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    passport_place_of_issue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    passport_issue_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ── Employee classification ─────────────────────────
    employee_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    employee_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Employment details ─────────────────────────────
    job_title: Mapped[str] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    soc_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    salary: Mapped[float] = mapped_column(Float, default=0)
    route: Mapped[str] = mapped_column(String(100), default="Skilled Worker")
    work_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_hybrid: Mapped[bool] = mapped_column(Boolean, default=False)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    termination_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ── Sponsorship & employment extras ───────────────
    work_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    sponsorship_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    visa_grant_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    job_application_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    offer_letter_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cos_assigned_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    bank_account_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Immigration details ────────────────────────────
    visa_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    passport_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    brp_reference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    brp_issue_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    brp_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_rtw_check: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_rtw_check: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    entry_clearance_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dbs_check_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ── Lifecycle & compliance ─────────────────────────
    status: Mapped[WorkerStatus] = mapped_column(SAEnum(WorkerStatus), default=WorkerStatus.ACTIVE)
    stage: Mapped[WorkerStage] = mapped_column(SAEnum(WorkerStage), default=WorkerStage.RECRUITMENT)
    risk_level: Mapped[RiskLevel] = mapped_column(SAEnum(RiskLevel), default=RiskLevel.LOW)

    # ── DBS / ATAS flags ──────────────────────────────
    dbs_required: Mapped[bool] = mapped_column(Boolean, default=False)
    dbs_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    atas_required: Mapped[bool] = mapped_column(Boolean, default=False)
    atas_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    organisation: Mapped["Organisation"] = relationship(back_populates="workers")
    portal_user: Mapped["User | None"] = relationship(back_populates="worker", foreign_keys="[User.worker_id]", uselist=False)
    cos_assignments: Mapped[list["CosAssignment"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
    recruitment: Mapped["Recruitment | None"] = relationship(back_populates="worker", uselist=False, cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
    salary_history: Mapped[list["SalaryHistory"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
    location_changes: Mapped[list["WorkLocationChange"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
    registrations: Mapped[list["ProfessionalRegistration"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
    contact_changes: Mapped[list["ContactDetailChange"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
    worker_requests: Mapped[list["WorkerRequest"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
    checklist_items: Mapped[list["DocumentChecklist"]] = relationship(back_populates="worker", cascade="all, delete-orphan")


# ═══════════════════════════════════════════════════════════
#  RECRUITMENT (Stage 1)
# ═══════════════════════════════════════════════════════════

class Recruitment(Base):
    __tablename__ = "recruitments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"), unique=True)

    # Job advert
    job_advert_uploaded: Mapped[bool] = mapped_column(Boolean, default=False)
    job_advert_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # RLMT / Resident Labour Market Test
    rlmt_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    rlmt_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    rlmt_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Genuine vacancy
    genuine_vacancy_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    genuine_vacancy_checklist: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Interview
    interview_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    interview_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Validation
    skill_level_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    salary_threshold_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    soc_code_validated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Vacancy approval
    vacancy_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="recruitment")


# ═══════════════════════════════════════════════════════════
#  COS ASSIGNMENT (Stage 2)
# ═══════════════════════════════════════════════════════════

class CosAssignment(Base):
    __tablename__ = "cos_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))

    cos_number: Mapped[str] = mapped_column(String(50), unique=True)
    cos_type: Mapped[CosType] = mapped_column(SAEnum(CosType), default=CosType.DEFINED)
    assigned_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    assigned_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ATAS
    atas_required: Mapped[bool] = mapped_column(Boolean, default=False)
    atas_certificate_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Immigration Skills Charge
    isc_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    isc_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Fee recovery compliance
    fee_recovery_compliant: Mapped[bool] = mapped_column(Boolean, default=True)

    # Flags
    close_relative_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    route_mismatch_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    salary_inconsistency_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_anomaly_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="cos_assignments")


# ═══════════════════════════════════════════════════════════
#  DOCUMENT (Appendix D compliant, versioned)
# ═══════════════════════════════════════════════════════════

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))

    doc_type: Mapped[str] = mapped_column(String(100))
    # passport, brp_evisa, right_to_work, employment_contract, salary_evidence,
    # ni_number_proof, registration_certificate, dbs_certificate, atas_certificate,
    # proof_of_address, job_advert, interview_notes, visa_decision, other

    status: Mapped[DocumentStatus] = mapped_column(SAEnum(DocumentStatus), default=DocumentStatus.PENDING)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)

    # File
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    file_mime: Mapped[str | None] = mapped_column(String(100), nullable=True)
    checklist_item_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("document_checklist.id"), nullable=True)

    # Metadata
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    upload_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_by_role: Mapped[str | None] = mapped_column(String(50), nullable=True)  # admin, employee
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="documents")
    checklist_item: Mapped["DocumentChecklist | None"] = relationship(back_populates="documents")


# ═══════════════════════════════════════════════════════════
#  DOCUMENT CHECKLIST (66 items per worker)
# ═══════════════════════════════════════════════════════════

class ChecklistStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    UPLOADED = "uploaded"
    VERIFIED = "verified"
    REJECTED = "rejected"
    NOT_APPLICABLE = "not_applicable"


class DocumentChecklist(Base):
    __tablename__ = "document_checklist"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))
    item_number: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[ChecklistStatus] = mapped_column(
        SAEnum(ChecklistStatus), default=ChecklistStatus.NOT_STARTED
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="checklist_items")
    documents: Mapped[list["Document"]] = relationship(back_populates="checklist_item")


# ═══════════════════════════════════════════════════════════
#  SALARY HISTORY
# ═══════════════════════════════════════════════════════════

class SalaryHistory(Base):
    __tablename__ = "salary_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))
    previous_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_salary: Mapped[float] = mapped_column(Float)
    effective_date: Mapped[datetime] = mapped_column(DateTime)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    below_threshold_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    changed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="salary_history")


# ═══════════════════════════════════════════════════════════
#  ATTENDANCE / ABSENCE TRACKING
# ═══════════════════════════════════════════════════════════

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))
    absence_type: Mapped[AbsenceType] = mapped_column(SAEnum(AbsenceType))
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    authorised: Mapped[bool] = mapped_column(Boolean, default=False)
    authorised_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Compliance flags
    exceeds_10_days: Mapped[bool] = mapped_column(Boolean, default=False)
    unpaid_exceeds_4_weeks: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="attendance_records")


# ═══════════════════════════════════════════════════════════
#  WORK LOCATION CHANGE
# ═══════════════════════════════════════════════════════════

class WorkLocationChange(Base):
    __tablename__ = "work_location_changes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))
    previous_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_location: Mapped[str] = mapped_column(String(255))
    effective_date: Mapped[datetime] = mapped_column(DateTime)
    reported_to_ho: Mapped[bool] = mapped_column(Boolean, default=False)
    report_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reported_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="location_changes")


# ═══════════════════════════════════════════════════════════
#  PROFESSIONAL REGISTRATION (NMC, GMC, etc.)
# ═══════════════════════════════════════════════════════════

class ProfessionalRegistration(Base):
    __tablename__ = "professional_registrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))
    body_name: Mapped[str] = mapped_column(String(255))  # NMC, GMC, HCPC, etc.
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="registrations")


# ═══════════════════════════════════════════════════════════
#  ALERT (auto-generated compliance warnings)
# ═══════════════════════════════════════════════════════════

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))
    alert_type: Mapped[AlertType] = mapped_column(SAEnum(AlertType))
    severity: Mapped[AlertSeverity] = mapped_column(SAEnum(AlertSeverity), default=AlertSeverity.WARNING)
    message: Mapped[str] = mapped_column(Text)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="alerts")


# ═══════════════════════════════════════════════════════════
#  REPORT (10 & 20 working day Home Office reports)
# ═══════════════════════════════════════════════════════════

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))
    report_type: Mapped[str] = mapped_column(String(255))
    deadline_type: Mapped[ReportDeadlineType] = mapped_column(SAEnum(ReportDeadlineType))
    status: Mapped[ReportStatus] = mapped_column(SAEnum(ReportStatus), default=ReportStatus.PENDING)
    deadline: Mapped[datetime] = mapped_column(DateTime)

    # Submission
    submitted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    evidence_document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="reports")


# ═══════════════════════════════════════════════════════════
#  RISK ASSESSMENT (Annex C1, C2, C3 triggers)
# ═══════════════════════════════════════════════════════════

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organisation_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"))
    assessed_date: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    overall_score: Mapped[int] = mapped_column(Integer, default=100)
    category: Mapped[RiskCategory] = mapped_column(SAEnum(RiskCategory), default=RiskCategory.COMPLIANT)

    # Annex C trigger flags (JSON object storing each trigger as bool)
    annex_c1_triggers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    annex_c2_triggers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    annex_c3_triggers: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ═══════════════════════════════════════════════════════════
#  EMPLOYEE PORTAL — Contact Detail Changes (before/after)
# ═══════════════════════════════════════════════════════════

class ContactDetailChange(Base):
    __tablename__ = "contact_detail_changes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))
    field_name: Mapped[str] = mapped_column(String(100))  # address, phone, personal_email, emergency_contact
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text)
    status: Mapped[ContactChangeStatus] = mapped_column(SAEnum(ContactChangeStatus), default=ContactChangeStatus.PENDING_APPROVAL)
    worker_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="contact_changes")


# ═══════════════════════════════════════════════════════════
#  EMPLOYEE PORTAL — HR Requests to Workers
# ═══════════════════════════════════════════════════════════

class WorkerRequest(Base):
    __tablename__ = "worker_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[WorkerRequestStatus] = mapped_column(SAEnum(WorkerRequestStatus), default=WorkerRequestStatus.OPEN)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Auto-escalation
    escalation_days: Mapped[int] = mapped_column(Integer, default=7)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="worker_requests")


# ═══════════════════════════════════════════════════════════
#  NOTIFICATION (reminders, alerts sent to users/workers)
# ═══════════════════════════════════════════════════════════

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("workers.id"), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    notification_type: Mapped[str] = mapped_column(String(100))  # visa_reminder, doc_expiry, request, system
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    worker: Mapped["Worker | None"] = relationship(back_populates="notifications")


# ═══════════════════════════════════════════════════════════
#  AUDIT LOG (immutable — every action in the system)
# ═══════════════════════════════════════════════════════════

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(50), nullable=True)

    action: Mapped[str] = mapped_column(String(255))
    # LOGIN, LOGOUT, VIEW, CREATE, UPDATE, DELETE, UPLOAD, DOWNLOAD,
    # APPROVE, REJECT, SUBMIT, ACKNOWLEDGE, RESOLVE

    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ═══════════════════════════════════════════════════════════
#  INSPECTION PACK (generated on-demand)
# ═══════════════════════════════════════════════════════════

class InspectionPack(Base):
    __tablename__ = "inspection_packs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organisation_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"))
    worker_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("workers.id"), nullable=True)
    pack_type: Mapped[str] = mapped_column(String(50))  # company, worker
    generated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ═══════════════════════════════════════════════════════════
#  LEAVE REQUESTS
# ═══════════════════════════════════════════════════════════

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))
    organisation_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"))

    leave_type: Mapped[LeaveType] = mapped_column(SAEnum(LeaveType), default=LeaveType.ANNUAL)
    start_date: Mapped[datetime] = mapped_column(Date)
    end_date: Mapped[datetime] = mapped_column(Date)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[LeaveStatus] = mapped_column(SAEnum(LeaveStatus), default=LeaveStatus.PENDING)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="leave_requests")


# Add relationship to Worker
Worker.leave_requests = relationship("LeaveRequest", back_populates="worker", lazy="dynamic")


# ═══════════════════════════════════════════════════════════
#  HOLIDAYS (company calendar)
# ═══════════════════════════════════════════════════════════

class Holiday(Base):
    __tablename__ = "holidays"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organisation_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"))
    name: Mapped[str] = mapped_column(String(255))
    date: Mapped[datetime] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


# ═══════════════════════════════════════════════════════════
#  BACKGROUND VERIFICATION
# ═══════════════════════════════════════════════════════════

class BgVerificationStatus(str, enum.Enum):
    PENDING_REFERENCES = "pending_references"
    EMAILS_SENT = "emails_sent"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ReferenceStatus(str, enum.Enum):
    DRAFT = "draft"
    EMAIL_SENT = "email_sent"
    COMPLETED = "completed"
    DECLINED = "declined"


class BgVerification(Base):
    __tablename__ = "bg_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"))
    organisation_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"))

    status: Mapped[BgVerificationStatus] = mapped_column(
        SAEnum(BgVerificationStatus), default=BgVerificationStatus.PENDING_REFERENCES
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    initiated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    worker: Mapped["Worker"] = relationship(back_populates="bg_verifications")
    references: Mapped[list["BgVerificationReference"]] = relationship(
        back_populates="verification", cascade="all, delete-orphan"
    )


class BgVerificationReference(Base):
    __tablename__ = "bg_verification_references"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    verification_id: Mapped[str] = mapped_column(String(36), ForeignKey("bg_verifications.id"))

    # Referee details (filled by employee)
    referee_name: Mapped[str] = mapped_column(String(255))
    referee_email: Mapped[str] = mapped_column(String(255))
    referee_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    referee_company: Mapped[str] = mapped_column(String(255))
    referee_job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    relation_to_employee: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employment_start: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    employment_end: Mapped[datetime | None] = mapped_column(Date, nullable=True)

    # Verification token (for the public link)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    status: Mapped[ReferenceStatus] = mapped_column(
        SAEnum(ReferenceStatus), default=ReferenceStatus.DRAFT
    )
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Response from referee
    response_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_confirm_employment: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    response_confirm_dates: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    response_confirm_title: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    response_recommend: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    response_reason_for_leaving: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_additional_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    verification: Mapped["BgVerification"] = relationship(back_populates="references")


Worker.bg_verifications = relationship("BgVerification", back_populates="worker", lazy="dynamic")
