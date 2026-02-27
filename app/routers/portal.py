"""Employee Portal endpoints — accessible by EMPLOYEE role."""

from datetime import datetime, timezone
import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.deps import get_current_user
from app.models.models import (
    User, Worker, UserRole, Document, DocumentStatus, ContactDetailChange,
    ContactChangeStatus, WorkerRequest, Notification, AuditLog,
    DocumentChecklist, ChecklistStatus,
)
from app.schemas.schemas import (
    WorkerDetailOut, DocumentOut, ContactChangeRequest, ContactChangeOut,
    WorkerRequestOut, NotificationOut,
)
from app.routers.documents import create_checklist_for_worker

router = APIRouter(prefix="/portal", tags=["employee-portal"])


def _get_employee_worker(current_user: User, db: Session) -> Worker:
    if current_user.role != UserRole.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Portal is for employees only")
    if not current_user.worker_id:
        raise HTTPException(status_code=404, detail="No worker record linked to this account")

    worker = db.query(Worker).filter(Worker.id == current_user.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker record not found")
    return worker


# ── My Profile ─────────────────────────────────────────────

@router.get("/me", response_model=WorkerDetailOut)
def get_my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    worker = _get_employee_worker(current_user, db)
    db.add(AuditLog(
        user_id=current_user.id, user_email=current_user.email, user_role="employee",
        action="VIEW", entity_type="worker", entity_id=worker.id,
        details="Worker viewed their sponsorship profile",
    ))
    db.commit()
    return worker


# ── My Documents ───────────────────────────────────────────

@router.get("/documents", response_model=list[DocumentOut])
def get_my_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    worker = _get_employee_worker(current_user, db)
    return db.query(Document).filter(Document.worker_id == worker.id).order_by(Document.created_at.desc()).all()


# ── Contact Detail Change Requests ─────────────────────────

@router.get("/contact-changes", response_model=list[ContactChangeOut])
def list_my_contact_changes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    worker = _get_employee_worker(current_user, db)
    return db.query(ContactDetailChange).filter(
        ContactDetailChange.worker_id == worker.id
    ).order_by(ContactDetailChange.created_at.desc()).all()


@router.post("/contact-changes", response_model=ContactChangeOut, status_code=status.HTTP_201_CREATED)
def request_contact_change(
    payload: ContactChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    worker = _get_employee_worker(current_user, db)

    allowed_fields = {"address", "phone", "personal_email", "emergency_contact_name", "emergency_contact_phone"}
    if payload.field_name not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"Cannot change field '{payload.field_name}'")

    old_value = getattr(worker, payload.field_name, None)

    change = ContactDetailChange(
        worker_id=worker.id,
        field_name=payload.field_name,
        old_value=str(old_value) if old_value else None,
        new_value=payload.new_value,
        worker_confirmed=True,
    )
    db.add(change)
    db.add(AuditLog(
        user_id=current_user.id, user_email=current_user.email, user_role="employee",
        action="UPDATE", entity_type="contact_detail_change", entity_id=change.id,
        details=f"Requested change: {payload.field_name}",
        before_value=str(old_value) if old_value else None,
        after_value=payload.new_value,
    ))
    db.commit()
    db.refresh(change)
    return change


# ── My Requests from HR ───────────────────────────────────

@router.get("/requests", response_model=list[WorkerRequestOut])
def list_my_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    worker = _get_employee_worker(current_user, db)
    return db.query(WorkerRequest).filter(
        WorkerRequest.worker_id == worker.id
    ).order_by(WorkerRequest.created_at.desc()).all()


# ── My Notifications ──────────────────────────────────────

@router.get("/notifications", response_model=list[NotificationOut])
def list_my_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    worker = _get_employee_worker(current_user, db)
    return db.query(Notification).filter(
        Notification.worker_id == worker.id
    ).order_by(Notification.created_at.desc()).limit(50).all()


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    worker = _get_employee_worker(current_user, db)
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.worker_id == worker.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "ok"}


# ── My Document Checklist ────────────────────────────────

@router.get("/checklist")
def get_my_checklist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    worker = _get_employee_worker(current_user, db)

    items = (
        db.query(DocumentChecklist)
        .filter(DocumentChecklist.worker_id == worker.id)
        .order_by(DocumentChecklist.item_number)
        .all()
    )
    if not items:
        items = create_checklist_for_worker(db, worker.id)
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
                    "notes": d.notes,
                }
                for d in docs
            ],
        })

    return result


@router.post("/checklist/{item_id}/upload")
async def portal_upload_document(
    item_id: str,
    file: UploadFile = File(...),
    notes: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    worker = _get_employee_worker(current_user, db)

    checklist_item = db.query(DocumentChecklist).filter(
        DocumentChecklist.id == item_id,
        DocumentChecklist.worker_id == worker.id,
    ).first()
    if not checklist_item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    file_bytes = await file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    doc = Document(
        worker_id=worker.id,
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
        uploaded_by_role="employee",
        notes=notes,
    )
    db.add(doc)

    checklist_item.status = ChecklistStatus.UPLOADED
    checklist_item.rejection_reason = None

    db.commit()

    return {"id": doc.id, "file_name": doc.file_name, "status": checklist_item.status.value}


@router.get("/checklist/{item_id}/download/{doc_id}")
def portal_download_document(
    item_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    worker = _get_employee_worker(current_user, db)

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.checklist_item_id == item_id,
        Document.worker_id == worker.id,
    ).first()
    if not doc or not doc.file_data:
        raise HTTPException(status_code=404, detail="Document not found")

    return Response(
        content=doc.file_data,
        media_type=doc.file_mime or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'},
    )
