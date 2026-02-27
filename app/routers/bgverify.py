"""Background verification endpoints."""

import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.deps import get_current_user, require_staff
from app.models.models import (
    User, Worker, UserRole,
    BgVerification, BgVerificationStatus,
    BgVerificationReference, ReferenceStatus,
)

router = APIRouter(prefix="/bgverify", tags=["background-verification"])


class ReferenceCreate(BaseModel):
    referee_name: str
    referee_email: str
    referee_phone: str | None = None
    referee_company: str
    referee_job_title: str | None = None
    relation_to_employee: str | None = None
    employment_start: str | None = None
    employment_end: str | None = None


class ReferenceResponse(BaseModel):
    confirm_employment: bool
    confirm_dates: bool
    confirm_title: bool
    recommend: bool
    rating: int | None = None
    reason_for_leaving: str | None = None
    comments: str | None = None
    additional_comments: str | None = None


def _ref_dict(ref: BgVerificationReference) -> dict:
    return {
        "id": ref.id,
        "referee_name": ref.referee_name,
        "referee_email": ref.referee_email,
        "referee_phone": ref.referee_phone,
        "referee_company": ref.referee_company,
        "referee_job_title": ref.referee_job_title,
        "relation_to_employee": ref.relation_to_employee,
        "employment_start": ref.employment_start.isoformat() if ref.employment_start else None,
        "employment_end": ref.employment_end.isoformat() if ref.employment_end else None,
        "status": ref.status.value,
        "email_sent_at": ref.email_sent_at.isoformat() if ref.email_sent_at else None,
        "response_rating": ref.response_rating,
        "response_comments": ref.response_comments,
        "response_confirm_employment": ref.response_confirm_employment,
        "response_confirm_dates": ref.response_confirm_dates,
        "response_confirm_title": ref.response_confirm_title,
        "response_recommend": ref.response_recommend,
        "response_reason_for_leaving": ref.response_reason_for_leaving,
        "response_additional_comments": ref.response_additional_comments,
        "responded_at": ref.responded_at.isoformat() if ref.responded_at else None,
        "token": ref.token,
    }


def _verify_dict(v: BgVerification, refs: list) -> dict:
    return {
        "id": v.id,
        "worker_id": v.worker_id,
        "status": v.status.value,
        "notes": v.notes,
        "initiated_by": v.initiated_by,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "references": [_ref_dict(r) for r in refs],
    }


# ── Get or create verification for a worker ──

@router.get("/worker/{worker_id}")
def get_verification(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    if current_user.role == UserRole.EMPLOYEE and current_user.worker_id != worker_id:
        raise HTTPException(status_code=403, detail="Access denied")

    v = (
        db.query(BgVerification)
        .filter(BgVerification.worker_id == worker_id)
        .order_by(BgVerification.created_at.desc())
        .first()
    )
    if not v:
        return {"id": None, "status": None, "references": []}

    refs = (
        db.query(BgVerificationReference)
        .filter(BgVerificationReference.verification_id == v.id)
        .order_by(BgVerificationReference.created_at)
        .all()
    )
    return _verify_dict(v, refs)


# ── Initiate BG verification for a worker (HR/admin) ──

@router.post("/worker/{worker_id}/initiate", status_code=status.HTTP_201_CREATED)
def initiate_verification(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    existing = (
        db.query(BgVerification)
        .filter(
            BgVerification.worker_id == worker_id,
            BgVerification.status.notin_([BgVerificationStatus.COMPLETED, BgVerificationStatus.FAILED]),
        )
        .first()
    )
    if existing:
        refs = (
            db.query(BgVerificationReference)
            .filter(BgVerificationReference.verification_id == existing.id)
            .all()
        )
        return _verify_dict(existing, refs)

    v = BgVerification(
        worker_id=worker_id,
        organisation_id=current_user.organisation_id,
        initiated_by=current_user.full_name,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return _verify_dict(v, [])


# ── Add a reference (employee or staff) ──

@router.post("/worker/{worker_id}/references")
def add_reference(
    worker_id: str,
    payload: ReferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.EMPLOYEE and current_user.worker_id != worker_id:
        raise HTTPException(status_code=403, detail="Access denied")

    v = (
        db.query(BgVerification)
        .filter(BgVerification.worker_id == worker_id)
        .order_by(BgVerification.created_at.desc())
        .first()
    )
    if not v:
        raise HTTPException(status_code=404, detail="No verification initiated for this worker")

    emp_start = None
    emp_end = None
    if payload.employment_start:
        try:
            emp_start = datetime.strptime(payload.employment_start, "%Y-%m-%d").date()
        except ValueError:
            pass
    if payload.employment_end:
        try:
            emp_end = datetime.strptime(payload.employment_end, "%Y-%m-%d").date()
        except ValueError:
            pass

    ref = BgVerificationReference(
        verification_id=v.id,
        referee_name=payload.referee_name,
        referee_email=payload.referee_email,
        referee_phone=payload.referee_phone,
        referee_company=payload.referee_company,
        referee_job_title=payload.referee_job_title,
        relation_to_employee=payload.relation_to_employee,
        employment_start=emp_start,
        employment_end=emp_end,
        token=secrets.token_urlsafe(32),
    )
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return _ref_dict(ref)


# ── Delete a reference (staff only, only if not yet completed) ──

@router.delete("/references/{ref_id}")
def delete_reference(
    ref_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    ref = db.query(BgVerificationReference).filter(BgVerificationReference.id == ref_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")
    if ref.status == ReferenceStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot delete a completed reference")
    db.delete(ref)
    db.commit()
    return {"status": "deleted"}


# ── Send verification emails (HR/admin) ──

@router.post("/worker/{worker_id}/send-emails")
def send_verification_emails(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    v = (
        db.query(BgVerification)
        .filter(BgVerification.worker_id == worker_id)
        .order_by(BgVerification.created_at.desc())
        .first()
    )
    if not v:
        raise HTTPException(status_code=404, detail="No verification found")

    refs = (
        db.query(BgVerificationReference)
        .filter(
            BgVerificationReference.verification_id == v.id,
            BgVerificationReference.status == ReferenceStatus.DRAFT,
        )
        .all()
    )
    if not refs:
        raise HTTPException(status_code=400, detail="No draft references to send")

    sent = 0
    for ref in refs:
        ref.status = ReferenceStatus.EMAIL_SENT
        ref.email_sent_at = datetime.now(timezone.utc)
        sent += 1

    v.status = BgVerificationStatus.EMAILS_SENT
    db.commit()

    return {
        "sent": sent,
        "message": f"Verification emails marked as sent for {sent} referee(s). "
                   "In production, real emails would be dispatched here.",
        "links": [
            {
                "referee": r.referee_name,
                "email": r.referee_email,
                "verification_url": f"/verify/{r.token}",
            }
            for r in refs
        ],
    }


# ── Public: get reference info by token (no auth) ──

@router.get("/public/{token}")
def get_reference_by_token(token: str, db: Session = Depends(get_db)):
    ref = db.query(BgVerificationReference).filter(BgVerificationReference.token == token).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Verification link not found or expired")

    if ref.status == ReferenceStatus.COMPLETED:
        return {"completed": True, "message": "This reference has already been submitted. Thank you!"}

    if ref.status == ReferenceStatus.DECLINED:
        return {"completed": True, "message": "This reference was declined."}

    v = db.query(BgVerification).filter(BgVerification.id == ref.verification_id).first()
    worker = db.query(Worker).filter(Worker.id == v.worker_id).first() if v else None

    return {
        "completed": False,
        "referee_name": ref.referee_name,
        "employee_name": worker.name if worker else "Unknown",
        "employee_job_title": worker.job_title if worker else "",
        "referee_company": ref.referee_company,
        "employment_start": ref.employment_start.isoformat() if ref.employment_start else None,
        "employment_end": ref.employment_end.isoformat() if ref.employment_end else None,
    }


# ── Public: submit reference response (no auth) ──

@router.post("/public/{token}/submit")
def submit_reference(token: str, payload: ReferenceResponse, db: Session = Depends(get_db)):
    ref = db.query(BgVerificationReference).filter(BgVerificationReference.token == token).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Verification link not found")

    if ref.status == ReferenceStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Already submitted")

    ref.response_confirm_employment = payload.confirm_employment
    ref.response_confirm_dates = payload.confirm_dates
    ref.response_confirm_title = payload.confirm_title
    ref.response_recommend = payload.recommend
    ref.response_rating = payload.rating
    ref.response_comments = payload.comments
    ref.response_reason_for_leaving = payload.reason_for_leaving
    ref.response_additional_comments = payload.additional_comments
    ref.responded_at = datetime.now(timezone.utc)
    ref.status = ReferenceStatus.COMPLETED

    v = db.query(BgVerification).filter(BgVerification.id == ref.verification_id).first()
    if v:
        all_refs = (
            db.query(BgVerificationReference)
            .filter(BgVerificationReference.verification_id == v.id)
            .all()
        )
        all_done = all(r.status in (ReferenceStatus.COMPLETED, ReferenceStatus.DECLINED) for r in all_refs)
        if all_done:
            v.status = BgVerificationStatus.COMPLETED
        else:
            v.status = BgVerificationStatus.IN_PROGRESS

    db.commit()
    return {"status": "submitted", "message": "Thank you for submitting your reference."}


# ── Public: decline reference (no auth) ──

@router.post("/public/{token}/decline")
def decline_reference(token: str, db: Session = Depends(get_db)):
    ref = db.query(BgVerificationReference).filter(BgVerificationReference.token == token).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Verification link not found")

    if ref.status == ReferenceStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Already submitted")

    ref.status = ReferenceStatus.DECLINED
    ref.responded_at = datetime.now(timezone.utc)

    v = db.query(BgVerification).filter(BgVerification.id == ref.verification_id).first()
    if v:
        all_refs = (
            db.query(BgVerificationReference)
            .filter(BgVerificationReference.verification_id == v.id)
            .all()
        )
        all_done = all(r.status in (ReferenceStatus.COMPLETED, ReferenceStatus.DECLINED) for r in all_refs)
        if all_done:
            v.status = BgVerificationStatus.COMPLETED

    db.commit()
    return {"status": "declined"}


# ── HR: mark verification as complete/failed ──

@router.post("/worker/{worker_id}/complete")
def complete_verification(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    v = (
        db.query(BgVerification)
        .filter(BgVerification.worker_id == worker_id)
        .order_by(BgVerification.created_at.desc())
        .first()
    )
    if not v:
        raise HTTPException(status_code=404, detail="No verification found")
    v.status = BgVerificationStatus.COMPLETED
    db.commit()
    return {"status": "completed"}


@router.post("/worker/{worker_id}/fail")
def fail_verification(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    v = (
        db.query(BgVerification)
        .filter(BgVerification.worker_id == worker_id)
        .order_by(BgVerification.created_at.desc())
        .first()
    )
    if not v:
        raise HTTPException(status_code=404, detail="No verification found")
    v.status = BgVerificationStatus.FAILED
    db.commit()
    return {"status": "failed"}
