"""Leave management endpoints — employees apply, HR/admin approve or reject."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.deps import get_current_user, require_staff
from app.models.models import User, Worker, UserRole, LeaveRequest, LeaveStatus, LeaveType

router = APIRouter(prefix="/leave", tags=["leave"])


class LeaveApplyRequest(BaseModel):
    leave_type: str
    start_date: str
    end_date: str
    reason: str | None = None


class LeaveActionRequest(BaseModel):
    rejection_reason: str | None = None


# ── Employee: apply for leave ──

@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def apply_leave(
    payload: LeaveApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.EMPLOYEE or not current_user.worker_id:
        raise HTTPException(status_code=403, detail="Only employees can apply for leave")

    worker = db.query(Worker).filter(Worker.id == current_user.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker record not found")

    try:
        start = datetime.strptime(payload.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(payload.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be YYYY-MM-DD format")

    if end < start:
        raise HTTPException(status_code=400, detail="End date must be on or after start date")

    try:
        leave_type = LeaveType(payload.leave_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid leave type: {payload.leave_type}")

    leave = LeaveRequest(
        worker_id=worker.id,
        organisation_id=worker.organisation_id,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        reason=payload.reason,
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)

    return _leave_to_dict(leave, worker)


# ── Employee: my leave history ──

@router.get("/my")
def my_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.EMPLOYEE or not current_user.worker_id:
        raise HTTPException(status_code=403, detail="Only employees can view their leave")

    worker = db.query(Worker).filter(Worker.id == current_user.worker_id).first()
    if not worker:
        return []

    leaves = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.worker_id == worker.id)
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )
    return [_leave_to_dict(l, worker) for l in leaves]


# ── Employee: cancel own pending leave ──

@router.post("/{leave_id}/cancel")
def cancel_leave(
    leave_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.EMPLOYEE or not current_user.worker_id:
        raise HTTPException(status_code=403, detail="Only employees can cancel their leave")

    leave = db.query(LeaveRequest).filter(
        LeaveRequest.id == leave_id,
        LeaveRequest.worker_id == current_user.worker_id,
    ).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending requests can be cancelled")

    leave.status = LeaveStatus.CANCELLED
    leave.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "cancelled"}


# ── HR/Admin: list all leave requests ──

@router.get("/all")
def list_all_leaves(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    query = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.organisation_id == current_user.organisation_id)
    )

    if status_filter:
        try:
            st = LeaveStatus(status_filter)
            query = query.filter(LeaveRequest.status == st)
        except ValueError:
            pass

    leaves = query.order_by(LeaveRequest.created_at.desc()).all()

    result = []
    worker_cache: dict[str, Worker] = {}
    for leave in leaves:
        if leave.worker_id not in worker_cache:
            w = db.query(Worker).filter(Worker.id == leave.worker_id).first()
            if w:
                worker_cache[leave.worker_id] = w
        worker = worker_cache.get(leave.worker_id)
        if worker:
            result.append(_leave_to_dict(leave, worker))

    return result


# ── HR/Admin: approve leave ──

@router.post("/{leave_id}/approve")
def approve_leave(
    leave_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    leave = db.query(LeaveRequest).filter(
        LeaveRequest.id == leave_id,
        LeaveRequest.organisation_id == current_user.organisation_id,
    ).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending requests can be approved")

    leave.status = LeaveStatus.APPROVED
    leave.reviewed_by = current_user.full_name
    leave.reviewed_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "approved"}


# ── HR/Admin: reject leave ──

@router.post("/{leave_id}/reject")
def reject_leave(
    leave_id: str,
    payload: LeaveActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    leave = db.query(LeaveRequest).filter(
        LeaveRequest.id == leave_id,
        LeaveRequest.organisation_id == current_user.organisation_id,
    ).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending requests can be rejected")

    leave.status = LeaveStatus.REJECTED
    leave.reviewed_by = current_user.full_name
    leave.reviewed_at = datetime.now(timezone.utc)
    leave.rejection_reason = payload.rejection_reason
    db.commit()

    return {"status": "rejected"}


def _leave_to_dict(leave: LeaveRequest, worker: Worker) -> dict:
    days = (leave.end_date - leave.start_date).days + 1
    return {
        "id": leave.id,
        "worker_id": leave.worker_id,
        "worker_name": worker.name,
        "worker_department": worker.department,
        "worker_job_title": worker.job_title,
        "leave_type": leave.leave_type.value,
        "start_date": leave.start_date.isoformat(),
        "end_date": leave.end_date.isoformat(),
        "days": days,
        "reason": leave.reason,
        "status": leave.status.value,
        "reviewed_by": leave.reviewed_by,
        "reviewed_at": leave.reviewed_at.isoformat() if leave.reviewed_at else None,
        "rejection_reason": leave.rejection_reason,
        "created_at": leave.created_at.isoformat() if leave.created_at else None,
    }
