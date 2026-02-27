import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.deps import get_current_user, require_staff
from app.models.models import (
    User, Worker, UserRole, Document, DocumentStatus,
    DocumentChecklist, ChecklistStatus,
)

router = APIRouter(prefix="/workers/{worker_id}/checklist", tags=["documents"])

# ──────────────────────────────────────────────────────────
# The 66 compliance checklist items
# ──────────────────────────────────────────────────────────

CHECKLIST_ITEMS: list[dict] = [
    {"n": 1, "desc": "A screenshot of the job advert, or the link to the job advert"},
    {"n": 2, "desc": "Confirmation that SOC Occupation code matches the job profile"},
    {"n": 3, "desc": "Confirmation of the genuineness of the job - the job role is genuine and is required based on the business's needs or for growth"},
    {"n": 4, "desc": "Details of the advertised job"},
    {"n": 5, "desc": "Details of the number of applicants who applied for the job, and shortlisted candidates uploaded"},
    {"n": 6, "desc": "A copy or summary of the interview notes for the successful candidate uploaded"},
    {"n": 7, "desc": "A list of common interview questions used for all candidates as part of your selection process"},
    {"n": 8, "desc": "Selection criteria for the successful candidate uploaded"},
    {"n": 9, "desc": "Scoring criteria to identify the successful candidate uploaded"},
    {"n": 10, "desc": "Sponsored Employee's CV reviewed and uploaded"},
    {"n": 11, "desc": "Completed Job Application Form reviewed and uploaded"},
    {"n": 12, "desc": "Right to Work check recorded on IRS HR"},
    {"n": 13, "desc": "Right to Work check PDF uploaded in the documents folder"},
    {"n": 14, "desc": "Proof of 3-month experience with the sponsoring company (only for international students, dependents and Post Study Work Visa holders in the UK) uploaded"},
    {"n": 15, "desc": "Employment Experience Letter reviewed and uploaded"},
    {"n": 16, "desc": "Recent practice in English reviewed and uploaded, if applicable"},
    {"n": 17, "desc": "A degree or qualification/training certificate reviewed and uploaded"},
    {"n": 18, "desc": "Sponsored Employee meets RQF Level 6 reviewed and requirement"},
    {"n": 19, "desc": "Reference from a previous employer reviewed and uploaded"},
    {"n": 20, "desc": "Other evidence of experience reviewed and uploaded"},
    {"n": 21, "desc": "Professional accreditation documents reviewed and uploaded, if applicable"},
    {"n": 22, "desc": "Passport reviewed and uploaded"},
    {"n": 23, "desc": "National Identity reviewed and uploaded, if applicable"},
    {"n": 24, "desc": "National insurance number recorded on IRS HR"},
    {"n": 25, "desc": "IELTS UKVI or OET Test Pass Certificate reviewed and uploaded"},
    {"n": 26, "desc": "Police Certificate reviewed and uploaded"},
    {"n": 27, "desc": "Signed Offer Letter reviewed and uploaded"},
    {"n": 28, "desc": "Signed Employment Contract reviewed and uploaded"},
    {"n": 29, "desc": "A detailed and specific job description uploaded"},
    {"n": 30, "desc": "Previous E-visa reviewed and uploaded in the documents folder if applicable"},
    {"n": 31, "desc": "Confirm that CoS was assigned after the interview was conducted and the Offer letter was issued"},
    {"n": 32, "desc": "New E-visa reviewed and uploaded in the documents folder"},
    {"n": 33, "desc": "Pension Joining letter of the employee reviewed and uploaded"},
    {"n": 34, "desc": "Pension leaving letter of the employee reviewed and uploaded, if applicable"},
    {"n": 35, "desc": "Employee induction completed"},
    {"n": 36, "desc": "Employee has received the Employee handbook"},
    {"n": 37, "desc": "Record of employee starting the sponsored employment on the start date listed on the CoS uploaded"},
    {"n": 38, "desc": "Monthly record of salary payslips uploaded in the documents folder"},
    {"n": 39, "desc": "Emergency Contact details recorded on IRS HR"},
    {"n": 40, "desc": "Next of kin details recorded on IRS HR"},
    {"n": 41, "desc": "Medical test certificate uploaded"},
    {"n": 42, "desc": "Evidence of current address (two required) reviewed and uploaded"},
    {"n": 43, "desc": "Confirm that the employee is being paid the annual salary listed in their CoS"},
    {"n": 44, "desc": "Confirm that the employee is being paid the annual salary more than the national living wage"},
    {"n": 45, "desc": "Supervision report uploaded"},
    {"n": 46, "desc": "Spot Check records uploaded"},
    {"n": 47, "desc": "Annual review uploaded"},
    {"n": 48, "desc": "Appraisal records uploaded"},
    {"n": 49, "desc": "Promotion letter issued and uploaded"},
    {"n": 50, "desc": "Evidence uploaded confirming sponsored employee performing duties listed in the CoS"},
    {"n": 51, "desc": "Change of work location updated in Reporting activities"},
    {"n": 52, "desc": "P60 issued and uploaded"},
    {"n": 53, "desc": "Salary Sacrifice agreement, if applicable"},
    {"n": 54, "desc": "Maternity leave documents reviewed and uploaded"},
    {"n": 55, "desc": "Paternity leave documents reviewed and uploaded"},
    {"n": 56, "desc": "Sick leave records uploaded"},
    {"n": 57, "desc": "Privacy and GDPR document reviewed and uploaded"},
    {"n": 58, "desc": "Exit interview uploaded"},
    {"n": 59, "desc": "Resignation letter/ Termination letter uploaded"},
    {"n": 60, "desc": "Gross conduct evidence uploaded, if applicable"},
    {"n": 61, "desc": "Disciplinary action record uploaded, if applicable"},
    {"n": 62, "desc": "Letter sent to the employee confirming the cessation of employment and sponsorship - a copy is uploaded"},
    {"n": 63, "desc": "Update the new visa end date"},
    {"n": 64, "desc": "Migrant Activity updated to confirm that the sponsored employee has left the employment"},
    {"n": 65, "desc": "Curtailment letter from the UKVI"},
    {"n": 66, "desc": "P45 issued and uploaded"},
]


def create_checklist_for_worker(db: Session, worker_id: str) -> list[DocumentChecklist]:
    """Auto-create all 66 checklist items for a newly created worker."""
    items = []
    for ci in CHECKLIST_ITEMS:
        item = DocumentChecklist(
            worker_id=worker_id,
            item_number=ci["n"],
            description=ci["desc"],
        )
        db.add(item)
        items.append(item)
    db.flush()
    return items


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def _get_worker(worker_id: str, db: Session, user: User) -> Worker:
    worker = db.query(Worker).filter(
        Worker.id == worker_id,
        Worker.organisation_id == user.organisation_id,
    ).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    if user.role == UserRole.EMPLOYEE and user.worker_id != worker_id:
        raise HTTPException(status_code=403, detail="You can only access your own records")
    return worker


# ──────────────────────────────────────────────────────────
# GET  /workers/{worker_id}/checklist
# ──────────────────────────────────────────────────────────

@router.get("")
def list_checklist(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_worker(worker_id, db, current_user)

    items = (
        db.query(DocumentChecklist)
        .filter(DocumentChecklist.worker_id == worker_id)
        .order_by(DocumentChecklist.item_number)
        .all()
    )

    if not items:
        items = create_checklist_for_worker(db, worker_id)
        db.commit()

    result = []
    for item in items:
        docs = (
            db.query(Document)
            .filter(Document.checklist_item_id == item.id)
            .order_by(Document.created_at.desc())
            .all()
        )
        result.append({
            "id": item.id,
            "item_number": item.item_number,
            "description": item.description,
            "status": item.status.value,
            "notes": item.notes,
            "verified_by": item.verified_by,
            "verified_at": item.verified_at.isoformat() if item.verified_at else None,
            "rejection_reason": item.rejection_reason,
            "documents": [
                {
                    "id": d.id,
                    "file_name": d.file_name,
                    "file_mime": d.file_mime,
                    "status": d.status.value,
                    "uploaded_by": d.uploaded_by,
                    "uploaded_by_role": d.uploaded_by_role,
                    "upload_date": d.upload_date.isoformat() if d.upload_date else None,
                    "verified_by": d.verified_by,
                    "verified_date": d.verified_date.isoformat() if d.verified_date else None,
                    "rejection_reason": d.rejection_reason,
                    "notes": d.notes,
                }
                for d in docs
            ],
        })

    return result


# ──────────────────────────────────────────────────────────
# POST  /workers/{worker_id}/checklist/{item_id}/upload
# ──────────────────────────────────────────────────────────

@router.post("/{item_id}/upload")
async def upload_document(
    worker_id: str,
    item_id: str,
    file: UploadFile = File(...),
    notes: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_worker(worker_id, db, current_user)

    checklist_item = db.query(DocumentChecklist).filter(
        DocumentChecklist.id == item_id,
        DocumentChecklist.worker_id == worker_id,
    ).first()
    if not checklist_item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    file_bytes = await file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    doc = Document(
        worker_id=worker_id,
        checklist_item_id=item_id,
        doc_type=f"checklist_{checklist_item.item_number}",
        status=DocumentStatus.PENDING,
        is_mandatory=True,
        file_name=file.filename,
        file_data=file_bytes,
        file_mime=file.content_type,
        file_hash=file_hash,
        upload_date=datetime.now(timezone.utc),
        uploaded_by=current_user.full_name,
        uploaded_by_role="employee" if current_user.role == UserRole.EMPLOYEE else "hr",
        notes=notes,
    )
    db.add(doc)

    checklist_item.status = ChecklistStatus.UPLOADED
    checklist_item.rejection_reason = None

    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "file_name": doc.file_name,
        "status": checklist_item.status.value,
        "message": "Document uploaded successfully",
    }


# ──────────────────────────────────────────────────────────
# GET  /workers/{worker_id}/checklist/{item_id}/download/{doc_id}
# ──────────────────────────────────────────────────────────

@router.get("/{item_id}/download/{doc_id}")
def download_document(
    worker_id: str,
    item_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_worker(worker_id, db, current_user)

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.checklist_item_id == item_id,
        Document.worker_id == worker_id,
    ).first()
    if not doc or not doc.file_data:
        raise HTTPException(status_code=404, detail="Document not found")

    return Response(
        content=doc.file_data,
        media_type=doc.file_mime or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'},
    )


# ──────────────────────────────────────────────────────────
# POST  /workers/{worker_id}/checklist/{item_id}/verify
# ──────────────────────────────────────────────────────────

@router.post("/{item_id}/verify")
def verify_checklist_item(
    worker_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    _get_worker(worker_id, db, current_user)

    checklist_item = db.query(DocumentChecklist).filter(
        DocumentChecklist.id == item_id,
        DocumentChecklist.worker_id == worker_id,
    ).first()
    if not checklist_item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    checklist_item.status = ChecklistStatus.VERIFIED
    checklist_item.verified_by = current_user.full_name
    checklist_item.verified_at = datetime.now(timezone.utc)
    checklist_item.rejection_reason = None

    docs = db.query(Document).filter(Document.checklist_item_id == item_id).all()
    for d in docs:
        d.status = DocumentStatus.VERIFIED
        d.verified_by = current_user.full_name
        d.verified_date = datetime.now(timezone.utc)

    db.commit()

    return {"status": "verified", "message": "Item verified successfully"}


# ──────────────────────────────────────────────────────────
# POST  /workers/{worker_id}/checklist/{item_id}/reject
# ──────────────────────────────────────────────────────────

@router.post("/{item_id}/reject")
def reject_checklist_item(
    worker_id: str,
    item_id: str,
    reason: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    _get_worker(worker_id, db, current_user)

    checklist_item = db.query(DocumentChecklist).filter(
        DocumentChecklist.id == item_id,
        DocumentChecklist.worker_id == worker_id,
    ).first()
    if not checklist_item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    checklist_item.status = ChecklistStatus.REJECTED
    checklist_item.rejection_reason = reason or "Rejected by HR"
    checklist_item.verified_by = None
    checklist_item.verified_at = None

    docs = db.query(Document).filter(Document.checklist_item_id == item_id).all()
    for d in docs:
        d.status = DocumentStatus.REJECTED
        d.rejection_reason = reason or "Rejected by HR"

    db.commit()

    return {"status": "rejected", "message": "Item rejected"}


# ──────────────────────────────────────────────────────────
# POST  /workers/{worker_id}/checklist/{item_id}/mark-na
# ──────────────────────────────────────────────────────────

@router.post("/{item_id}/mark-na")
def mark_not_applicable(
    worker_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    _get_worker(worker_id, db, current_user)

    checklist_item = db.query(DocumentChecklist).filter(
        DocumentChecklist.id == item_id,
        DocumentChecklist.worker_id == worker_id,
    ).first()
    if not checklist_item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    checklist_item.status = ChecklistStatus.NOT_APPLICABLE
    db.commit()

    return {"status": "not_applicable", "message": "Marked as not applicable"}


# ──────────────────────────────────────────────────────────
# POST  /workers/{worker_id}/checklist/{item_id}/notes
# ──────────────────────────────────────────────────────────

@router.post("/{item_id}/notes")
def update_notes(
    worker_id: str,
    item_id: str,
    notes: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_worker(worker_id, db, current_user)

    checklist_item = db.query(DocumentChecklist).filter(
        DocumentChecklist.id == item_id,
        DocumentChecklist.worker_id == worker_id,
    ).first()
    if not checklist_item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    checklist_item.notes = notes
    db.commit()

    return {"message": "Notes updated"}
