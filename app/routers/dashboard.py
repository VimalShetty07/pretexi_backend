from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.routers.deps import get_current_user
from app.models.models import (
    User, Worker, Alert, Report, Organisation, Document, LeaveRequest, LeaveStatus,
    AlertSeverity, ReportStatus, DocumentStatus, WorkerStatus,
)
from app.schemas.schemas import DashboardStats, AlertOut, ReportOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organisation_id
    org = db.query(Organisation).filter(Organisation.id == org_id).first()

    total_workers = db.query(Worker).filter(Worker.organisation_id == org_id).count()
    active_workers = db.query(Worker).filter(
        Worker.organisation_id == org_id, Worker.status == WorkerStatus.ACTIVE
    ).count()

    critical_alerts = db.query(Alert).join(Worker).filter(
        Worker.organisation_id == org_id,
        Alert.severity == AlertSeverity.CRITICAL,
        Alert.is_resolved == False,
    ).count()
    warning_alerts = db.query(Alert).join(Worker).filter(
        Worker.organisation_id == org_id,
        Alert.severity == AlertSeverity.WARNING,
        Alert.is_resolved == False,
    ).count()

    pending_reports = db.query(Report).join(Worker).filter(
        Worker.organisation_id == org_id,
        Report.status != ReportStatus.SUBMITTED,
    ).count()
    overdue_reports = db.query(Report).join(Worker).filter(
        Worker.organisation_id == org_id,
        Report.status == ReportStatus.OVERDUE,
    ).count()

    missing_documents = db.query(Document).join(Worker).filter(
        Worker.organisation_id == org_id,
        Document.status == DocumentStatus.MISSING,
    ).count()

    # Visas expiring within 90 days
    ninety_days = datetime.now(timezone.utc) + timedelta(days=90)
    expiring_visas = db.query(Worker).filter(
        Worker.organisation_id == org_id,
        Worker.status == WorkerStatus.ACTIVE,
        Worker.visa_expiry != None,
        Worker.visa_expiry <= ninety_days,
    ).count()

    return DashboardStats(
        total_workers=total_workers,
        active_workers=active_workers,
        critical_alerts=critical_alerts,
        warning_alerts=warning_alerts,
        pending_reports=pending_reports,
        overdue_reports=overdue_reports,
        health_score=org.health_score if org else 0,
        risk_category=org.risk_category.value if org else "compliant",
        cos_used=org.cos_used if org else 0,
        cos_allocated=org.cos_allocated if org else 0,
        missing_documents=missing_documents,
        expiring_visas=expiring_visas,
    )


@router.get("/overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organisation_id
    now = datetime.now(timezone.utc).date()
    org = db.query(Organisation).filter(Organisation.id == org_id).first()

    active_workers = (
        db.query(Worker)
        .filter(Worker.organisation_id == org_id, Worker.status == WorkerStatus.ACTIVE)
        .all()
    )

    sponsored = 0
    non_sponsored = 0
    expired = 0
    expiring_30 = 0
    expiring_60 = 0
    expiring_90 = 0
    valid = 0
    no_visa = 0
    expiring_workers: list[dict] = []

    for w in active_workers:
        if w.sponsorship_number or (w.route and w.route.lower() not in ("", "n/a", "none", "domestic")):
            sponsored += 1
        else:
            non_sponsored += 1

        if w.visa_expiry:
            visa_date = w.visa_expiry if hasattr(w.visa_expiry, 'date') is False else w.visa_expiry
            if hasattr(visa_date, 'date'):
                visa_date = visa_date.date()
            days_left = (visa_date - now).days

            if days_left <= 0:
                expired += 1
                expiring_workers.append({
                    "id": w.id, "name": w.name, "visa_expiry": w.visa_expiry.isoformat(),
                    "days_left": days_left, "category": "expired",
                    "department": w.department, "job_title": w.job_title,
                })
            elif days_left <= 30:
                expiring_30 += 1
                expiring_workers.append({
                    "id": w.id, "name": w.name, "visa_expiry": w.visa_expiry.isoformat(),
                    "days_left": days_left, "category": "30_days",
                    "department": w.department, "job_title": w.job_title,
                })
            elif days_left <= 60:
                expiring_60 += 1
                expiring_workers.append({
                    "id": w.id, "name": w.name, "visa_expiry": w.visa_expiry.isoformat(),
                    "days_left": days_left, "category": "60_days",
                    "department": w.department, "job_title": w.job_title,
                })
            elif days_left <= 90:
                expiring_90 += 1
                expiring_workers.append({
                    "id": w.id, "name": w.name, "visa_expiry": w.visa_expiry.isoformat(),
                    "days_left": days_left, "category": "90_days",
                    "department": w.department, "job_title": w.job_title,
                })
            else:
                valid += 1
        else:
            no_visa += 1

    total = db.query(Worker).filter(Worker.organisation_id == org_id).count()

    pending_leaves = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.organisation_id == org_id,
            LeaveRequest.status == LeaveStatus.PENDING,
        )
        .count()
    )

    expiring_workers.sort(key=lambda x: x["days_left"])

    # CoS outlook: how many additional CoS are required beyond current available allocation
    available_cos = 0
    if org:
        available_cos = max((org.cos_allocated or 0) - (org.cos_used or 0), 0)

    forecast_demand_90 = 0
    projected_demand_12m = 0
    for w in active_workers:
        is_sponsored_worker = bool(w.sponsorship_number) or (w.route and w.route.lower() not in ("", "n/a", "none", "domestic"))
        if not is_sponsored_worker or not w.visa_expiry:
            continue

        visa_date = w.visa_expiry.date() if hasattr(w.visa_expiry, "date") else w.visa_expiry
        days_left = (visa_date - now).days
        if 0 <= days_left <= 90:
            forecast_demand_90 += 1
        if 0 <= days_left <= 365:
            projected_demand_12m += 1

    cos_forecasted_required = max(forecast_demand_90 - available_cos, 0)
    cos_projected_required = max(projected_demand_12m - available_cos, 0)

    return {
        "total_employees": total,
        "active_employees": len(active_workers),
        "sponsored": sponsored,
        "non_sponsored": non_sponsored,
        "pending_leaves": pending_leaves,
        "cos_allocated": org.cos_allocated if org else 0,
        "cos_used": org.cos_used if org else 0,
        "cos_available": available_cos,
        "cos_forecasted_required": cos_forecasted_required,
        "cos_projected_required": cos_projected_required,
        "cos_forecasted_demand": forecast_demand_90,
        "cos_projected_demand": projected_demand_12m,
        "visa_breakdown": {
            "expired": expired,
            "expiring_30": expiring_30,
            "expiring_60": expiring_60,
            "expiring_90": expiring_90,
            "valid": valid,
            "no_visa": no_visa,
        },
        "expiring_workers": expiring_workers[:15],
    }


@router.get("/recent-alerts", response_model=list[AlertOut])
def get_recent_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Alert).join(Worker)
        .filter(Worker.organisation_id == current_user.organisation_id, Alert.is_resolved == False)
        .order_by(Alert.created_at.desc())
        .limit(10)
        .all()
    )


@router.get("/upcoming-reports", response_model=list[ReportOut])
def get_upcoming_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Report).join(Worker)
        .filter(Worker.organisation_id == current_user.organisation_id, Report.status != ReportStatus.SUBMITTED)
        .order_by(Report.deadline.asc())
        .limit(10)
        .all()
    )
