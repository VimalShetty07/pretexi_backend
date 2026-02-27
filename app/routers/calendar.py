"""Calendar endpoints — holidays (CRUD for staff, read for employees) + approved leaves."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.deps import get_current_user, require_staff
from app.models.models import (
    User,
    Worker,
    UserRole,
    Holiday,
    LeaveRequest,
    LeaveStatus,
    BgVerification,
    BgVerificationReference,
)

router = APIRouter(prefix="/calendar", tags=["calendar"])


class HolidayCreate(BaseModel):
    name: str
    date: str
    description: str | None = None


class HolidayUpdate(BaseModel):
    name: str | None = None
    date: str | None = None
    description: str | None = None


def _holiday_dict(h: Holiday) -> dict:
    return {
        "id": h.id,
        "name": h.name,
        "date": h.date.isoformat(),
        "description": h.description,
        "created_by": h.created_by,
        "type": "holiday",
    }


# ── List holidays ──

@router.get("/holidays")
def list_holidays(
    year: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Holiday).filter(Holiday.organisation_id == current_user.organisation_id)
    if year:
        from sqlalchemy import extract
        query = query.filter(extract("year", Holiday.date) == year)
    return [_holiday_dict(h) for h in query.order_by(Holiday.date).all()]


# ── Create holiday (staff only) ──

@router.post("/holidays", status_code=status.HTTP_201_CREATED)
def create_holiday(
    payload: HolidayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    try:
        date = datetime.strptime(payload.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Date must be YYYY-MM-DD")

    holiday = Holiday(
        organisation_id=current_user.organisation_id,
        name=payload.name,
        date=date,
        description=payload.description,
        created_by=current_user.full_name,
    )
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return _holiday_dict(holiday)


# ── Update holiday (staff only) ──

@router.patch("/holidays/{holiday_id}")
def update_holiday(
    holiday_id: str,
    payload: HolidayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    holiday = db.query(Holiday).filter(
        Holiday.id == holiday_id,
        Holiday.organisation_id == current_user.organisation_id,
    ).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")

    if payload.name is not None:
        holiday.name = payload.name
    if payload.description is not None:
        holiday.description = payload.description
    if payload.date is not None:
        try:
            holiday.date = datetime.strptime(payload.date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Date must be YYYY-MM-DD")

    db.commit()
    db.refresh(holiday)
    return _holiday_dict(holiday)


# ── Delete holiday (staff only) ──

@router.delete("/holidays/{holiday_id}")
def delete_holiday(
    holiday_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    holiday = db.query(Holiday).filter(
        Holiday.id == holiday_id,
        Holiday.organisation_id == current_user.organisation_id,
    ).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")

    db.delete(holiday)
    db.commit()
    return {"status": "deleted"}


# ── Calendar events (holidays + approved leaves for a month/year) ──

@router.get("/events")
def calendar_events(
    year: int,
    month: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import extract
    from datetime import date

    org_id = current_user.organisation_id

    # Holidays
    hq = db.query(Holiday).filter(
        Holiday.organisation_id == org_id,
        extract("year", Holiday.date) == year,
    )
    if month:
        hq = hq.filter(extract("month", Holiday.date) == month)
    holidays = [_holiday_dict(h) for h in hq.order_by(Holiday.date).all()]

    # Approved leaves
    lq = db.query(LeaveRequest).filter(
        LeaveRequest.organisation_id == org_id,
        LeaveRequest.status == LeaveStatus.APPROVED,
        extract("year", LeaveRequest.start_date) == year,
    )
    if month:
        lq = lq.filter(extract("month", LeaveRequest.start_date) == month)

    if current_user.role == UserRole.EMPLOYEE:
        if current_user.worker_id:
            lq = lq.filter(LeaveRequest.worker_id == current_user.worker_id)
        else:
            lq = lq.filter(False)

    leaves_result = []
    worker_cache: dict[str, Worker] = {}
    for leave in lq.order_by(LeaveRequest.start_date).all():
        if leave.worker_id not in worker_cache:
            w = db.query(Worker).filter(Worker.id == leave.worker_id).first()
            if w:
                worker_cache[leave.worker_id] = w
        worker = worker_cache.get(leave.worker_id)
        if worker:
            leaves_result.append({
                "id": leave.id,
                "worker_name": worker.name,
                "worker_department": worker.department,
                "leave_type": leave.leave_type.value,
                "start_date": leave.start_date.isoformat(),
                "end_date": leave.end_date.isoformat(),
                "days": (leave.end_date - leave.start_date).days + 1,
                "type": "leave",
            })

    # Visa expiry dates (staff/admin views)
    visa_expiries_result = []
    if current_user.role != UserRole.EMPLOYEE:
        vq = db.query(Worker).filter(
            Worker.organisation_id == org_id,
            Worker.visa_expiry != None,  # noqa: E711
            extract("year", Worker.visa_expiry) == year,
        )
        if month:
            vq = vq.filter(extract("month", Worker.visa_expiry) == month)

        today = date.today()
        for worker in vq.order_by(Worker.visa_expiry).all():
            if not worker.visa_expiry:
                continue
            expiry_date = worker.visa_expiry.date() if hasattr(worker.visa_expiry, "date") else worker.visa_expiry
            days_left = (expiry_date - today).days
            visa_expiries_result.append({
                "id": worker.id,
                "worker_name": worker.name,
                "worker_department": worker.department,
                "date": expiry_date.isoformat(),
                "days_left": days_left,
                "type": "visa_expiry",
            })

    # Background verification milestones (staff/admin views)
    bg_verifications_result = []
    if current_user.role != UserRole.EMPLOYEE:
        bq = (
            db.query(BgVerificationReference, BgVerification, Worker)
            .join(BgVerification, BgVerificationReference.verification_id == BgVerification.id)
            .join(Worker, BgVerification.worker_id == Worker.id)
            .filter(
                BgVerification.organisation_id == org_id,
                BgVerificationReference.employment_end != None,  # noqa: E711
                extract("year", BgVerificationReference.employment_end) == year,
            )
        )
        if month:
            bq = bq.filter(extract("month", BgVerificationReference.employment_end) == month)

        for ref, verification, worker in bq.order_by(BgVerificationReference.employment_end).all():
            bg_date = (
                ref.employment_end.isoformat()
                if hasattr(ref.employment_end, "isoformat")
                else str(ref.employment_end)
            )
            bg_verifications_result.append({
                "id": ref.id,
                "worker_id": worker.id,
                "worker_name": worker.name,
                "worker_department": worker.department,
                "referee_name": ref.referee_name,
                "date": bg_date,
                "reference_status": ref.status.value if ref.status else None,
                "verification_status": verification.status.value if verification.status else None,
                "type": "bg_verification",
            })

    return {
        "holidays": holidays,
        "leaves": leaves_result,
        "visa_expiries": visa_expiries_result,
        "bg_verifications": bg_verifications_result,
    }
