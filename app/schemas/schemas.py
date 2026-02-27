from pydantic import BaseModel
from datetime import datetime


# ═══════════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    identifier: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    organisation_name: str
    licence_number: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ═══════════════════════════════════════════════════════════
#  USER
# ═══════════════════════════════════════════════════════════

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    organisation_id: str
    worker_id: str | None = None
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str  # super_admin, compliance_manager, hr_officer, payroll_officer, inspector, employee
    worker_id: str | None = None  # only for employee role
    access_expires_at: datetime | None = None  # only for inspector role


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    phone: str | None = None


# ═══════════════════════════════════════════════════════════
#  ORGANISATION
# ═══════════════════════════════════════════════════════════

class OrganisationOut(BaseModel):
    id: str
    name: str
    licence_number: str
    rating: str
    cos_allocated: int
    cos_used: int
    address: str | None = None
    sector: str | None = None
    licence_expiry: datetime | None = None
    health_score: int
    risk_category: str
    authorised_officer: str | None = None
    portal_enabled: bool
    portal_require_edit_approval: bool

    class Config:
        from_attributes = True


class OrganisationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    sector: str | None = None
    cos_allocated: int | None = None
    authorised_officer: str | None = None
    portal_enabled: bool | None = None
    portal_show_cos_ref: bool | None = None
    portal_show_salary: bool | None = None
    portal_require_edit_approval: bool | None = None


# ═══════════════════════════════════════════════════════════
#  KEY PERSONNEL
# ═══════════════════════════════════════════════════════════

class KeyPersonnelCreate(BaseModel):
    name: str
    sms_role: str  # authorising_officer, level_1, level_2
    email: str | None = None
    phone: str | None = None


class KeyPersonnelOut(BaseModel):
    id: str
    name: str
    sms_role: str
    email: str | None = None
    phone: str | None = None
    is_active: bool
    added_date: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  WORKER
# ═══════════════════════════════════════════════════════════

class WorkerCreate(BaseModel):
    name: str
    first_name: str | None = None
    last_name: str | None = None
    job_title: str
    email: str | None = None
    phone: str | None = None
    personal_email: str | None = None
    nationality: str | None = None
    department: str | None = None
    soc_code: str | None = None
    salary: float = 0
    route: str = "Skilled Worker"
    work_location: str | None = None
    is_hybrid: bool = False
    is_remote: bool = False
    start_date: datetime | None = None
    visa_expiry: datetime | None = None
    passport_expiry: datetime | None = None
    brp_expiry: datetime | None = None
    dbs_required: bool = False
    atas_required: bool = False
    stage: str = "recruitment"
    address: str | None = None
    postal_code: str | None = None
    date_of_birth: datetime | None = None
    place_of_birth: str | None = None
    country_of_birth: str | None = None
    gender: str | None = None
    ethnicity: str | None = None
    religion: str | None = None
    ni_number: str | None = None
    passport_number: str | None = None
    passport_place_of_issue: str | None = None
    passport_issue_date: datetime | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    next_of_kin_name: str | None = None
    next_of_kin_phone: str | None = None
    employee_id: str | None = None
    employee_type: str | None = None
    work_address: str | None = None
    sponsorship_number: str | None = None
    visa_grant_date: datetime | None = None
    job_application_date: datetime | None = None
    offer_letter_date: datetime | None = None
    cos_assigned_date: datetime | None = None
    bank_account_number: str | None = None
    sort_code: str | None = None
    brp_reference: str | None = None
    brp_issue_date: datetime | None = None
    dbs_check_date: datetime | None = None


class WorkerUpdate(BaseModel):
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None
    email: str | None = None
    phone: str | None = None
    personal_email: str | None = None
    address: str | None = None
    postal_code: str | None = None
    nationality: str | None = None
    department: str | None = None
    soc_code: str | None = None
    salary: float | None = None
    route: str | None = None
    work_location: str | None = None
    is_hybrid: bool | None = None
    is_remote: bool | None = None
    start_date: datetime | None = None
    termination_date: datetime | None = None
    visa_expiry: datetime | None = None
    passport_expiry: datetime | None = None
    brp_expiry: datetime | None = None
    status: str | None = None
    stage: str | None = None
    risk_level: str | None = None
    dbs_required: bool | None = None
    dbs_completed: bool | None = None
    atas_required: bool | None = None
    atas_completed: bool | None = None
    date_of_birth: datetime | None = None
    place_of_birth: str | None = None
    country_of_birth: str | None = None
    gender: str | None = None
    ethnicity: str | None = None
    religion: str | None = None
    ni_number: str | None = None
    passport_number: str | None = None
    passport_place_of_issue: str | None = None
    passport_issue_date: datetime | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    next_of_kin_name: str | None = None
    next_of_kin_phone: str | None = None
    employee_id: str | None = None
    employee_type: str | None = None
    work_address: str | None = None
    sponsorship_number: str | None = None
    visa_grant_date: datetime | None = None
    job_application_date: datetime | None = None
    offer_letter_date: datetime | None = None
    cos_assigned_date: datetime | None = None
    bank_account_number: str | None = None
    sort_code: str | None = None
    brp_reference: str | None = None
    brp_issue_date: datetime | None = None
    dbs_check_date: datetime | None = None


class WorkerOut(BaseModel):
    id: str
    name: str
    job_title: str
    email: str | None = None
    phone: str | None = None
    nationality: str | None = None
    department: str | None = None
    soc_code: str | None = None
    salary: float
    route: str
    work_location: str | None = None
    is_hybrid: bool
    is_remote: bool
    start_date: datetime | None = None
    termination_date: datetime | None = None
    visa_expiry: datetime | None = None
    passport_expiry: datetime | None = None
    brp_expiry: datetime | None = None
    status: str
    stage: str
    risk_level: str
    dbs_required: bool
    atas_required: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WorkerDetailOut(WorkerOut):
    """Extended worker output for detail page — includes personal + portal fields."""
    first_name: str | None = None
    last_name: str | None = None
    personal_email: str | None = None
    address: str | None = None
    postal_code: str | None = None
    date_of_birth: datetime | None = None
    place_of_birth: str | None = None
    country_of_birth: str | None = None
    gender: str | None = None
    ethnicity: str | None = None
    religion: str | None = None
    ni_number: str | None = None
    passport_number: str | None = None
    passport_place_of_issue: str | None = None
    passport_issue_date: datetime | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    next_of_kin_name: str | None = None
    next_of_kin_phone: str | None = None
    employee_id: str | None = None
    employee_type: str | None = None
    entry_clearance_date: datetime | None = None
    last_rtw_check: datetime | None = None
    next_rtw_check: datetime | None = None
    dbs_completed: bool = False
    atas_completed: bool = False
    work_address: str | None = None
    sponsorship_number: str | None = None
    visa_grant_date: datetime | None = None
    job_application_date: datetime | None = None
    offer_letter_date: datetime | None = None
    cos_assigned_date: datetime | None = None
    bank_account_number: str | None = None
    sort_code: str | None = None
    brp_reference: str | None = None
    brp_issue_date: datetime | None = None
    dbs_check_date: datetime | None = None


# ═══════════════════════════════════════════════════════════
#  RECRUITMENT
# ═══════════════════════════════════════════════════════════

class RecruitmentCreate(BaseModel):
    worker_id: str
    job_advert_uploaded: bool = False
    rlmt_applicable: bool = False
    interview_date: datetime | None = None
    interview_notes: str | None = None


class RecruitmentUpdate(BaseModel):
    job_advert_uploaded: bool | None = None
    job_advert_url: str | None = None
    rlmt_applicable: bool | None = None
    rlmt_completed: bool | None = None
    rlmt_notes: str | None = None
    genuine_vacancy_confirmed: bool | None = None
    genuine_vacancy_checklist: dict | None = None
    interview_date: datetime | None = None
    interview_notes: str | None = None
    skill_level_validated: bool | None = None
    salary_threshold_validated: bool | None = None
    soc_code_validated: bool | None = None
    vacancy_approved: bool | None = None
    approved_by: str | None = None


class RecruitmentOut(BaseModel):
    id: str
    worker_id: str
    job_advert_uploaded: bool
    rlmt_applicable: bool
    rlmt_completed: bool
    genuine_vacancy_confirmed: bool
    skill_level_validated: bool
    salary_threshold_validated: bool
    soc_code_validated: bool
    vacancy_approved: bool
    approved_by: str | None = None
    approved_date: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  COS ASSIGNMENT
# ═══════════════════════════════════════════════════════════

class CosAssignmentCreate(BaseModel):
    worker_id: str
    cos_number: str
    cos_type: str = "defined"
    assigned_date: datetime | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    atas_required: bool = False
    isc_paid: bool = False
    isc_amount: float | None = None


class CosAssignmentOut(BaseModel):
    id: str
    worker_id: str
    cos_number: str
    cos_type: str
    assigned_date: datetime | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    atas_required: bool
    isc_paid: bool
    fee_recovery_compliant: bool
    close_relative_flag: bool
    route_mismatch_flag: bool
    salary_inconsistency_flag: bool
    duration_anomaly_flag: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  DOCUMENT
# ═══════════════════════════════════════════════════════════

class DocumentCreate(BaseModel):
    worker_id: str
    doc_type: str
    is_mandatory: bool = False
    expiry_date: datetime | None = None
    notes: str | None = None


class DocumentOut(BaseModel):
    id: str
    worker_id: str
    doc_type: str
    status: str
    is_mandatory: bool
    file_name: str | None = None
    expiry_date: datetime | None = None
    upload_date: datetime | None = None
    uploaded_by: str | None = None
    uploaded_by_role: str | None = None
    verified_by: str | None = None
    verified_date: datetime | None = None
    rejection_reason: str | None = None
    version: int
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  SALARY HISTORY
# ═══════════════════════════════════════════════════════════

class SalaryChangeCreate(BaseModel):
    worker_id: str
    new_salary: float
    effective_date: datetime
    reason: str | None = None


class SalaryHistoryOut(BaseModel):
    id: str
    worker_id: str
    previous_salary: float | None = None
    new_salary: float
    effective_date: datetime
    reason: str | None = None
    below_threshold_flag: bool
    changed_by: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  ATTENDANCE
# ═══════════════════════════════════════════════════════════

class AttendanceCreate(BaseModel):
    worker_id: str
    absence_type: str
    start_date: datetime
    end_date: datetime | None = None
    total_days: int | None = None
    reason: str | None = None
    authorised: bool = False


class AttendanceOut(BaseModel):
    id: str
    worker_id: str
    absence_type: str
    start_date: datetime
    end_date: datetime | None = None
    total_days: int | None = None
    reason: str | None = None
    authorised: bool
    exceeds_10_days: bool
    unpaid_exceeds_4_weeks: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  ALERT
# ═══════════════════════════════════════════════════════════

class AlertOut(BaseModel):
    id: str
    worker_id: str
    alert_type: str
    severity: str
    message: str
    due_date: datetime | None = None
    is_resolved: bool
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  REPORT (10/20 working day)
# ═══════════════════════════════════════════════════════════

class ReportCreate(BaseModel):
    worker_id: str
    report_type: str
    deadline_type: str  # 10_working_days, 20_working_days
    deadline: datetime
    notes: str | None = None


class ReportOut(BaseModel):
    id: str
    worker_id: str
    report_type: str
    deadline_type: str
    status: str
    deadline: datetime
    submitted_by: str | None = None
    submitted_date: datetime | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  EMPLOYEE PORTAL — Contact Changes
# ═══════════════════════════════════════════════════════════

class ContactChangeRequest(BaseModel):
    field_name: str  # address, phone, personal_email, emergency_contact
    new_value: str


class ContactChangeOut(BaseModel):
    id: str
    worker_id: str
    field_name: str
    old_value: str | None = None
    new_value: str
    status: str
    worker_confirmed: bool
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  EMPLOYEE PORTAL — Worker Requests
# ═══════════════════════════════════════════════════════════

class WorkerRequestCreate(BaseModel):
    worker_id: str
    title: str
    description: str | None = None
    due_date: datetime | None = None
    escalation_days: int = 7


class WorkerRequestOut(BaseModel):
    id: str
    worker_id: str
    title: str
    description: str | None = None
    due_date: datetime | None = None
    status: str
    created_by: str | None = None
    escalation_days: int
    escalated: bool
    completed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  NOTIFICATION
# ═══════════════════════════════════════════════════════════

class NotificationOut(BaseModel):
    id: str
    worker_id: str | None = None
    user_id: str | None = None
    title: str
    message: str
    notification_type: str
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  AUDIT LOG
# ═══════════════════════════════════════════════════════════

class AuditLogOut(BaseModel):
    id: str
    user_id: str | None = None
    user_email: str | None = None
    user_role: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    details: str | None = None
    ip_address: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════

class DashboardStats(BaseModel):
    total_workers: int
    active_workers: int
    critical_alerts: int
    warning_alerts: int
    pending_reports: int
    overdue_reports: int
    health_score: int
    risk_category: str
    cos_used: int
    cos_allocated: int
    missing_documents: int
    expiring_visas: int
