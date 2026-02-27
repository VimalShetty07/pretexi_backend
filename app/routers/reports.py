from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import get_db
from app.routers.deps import get_current_user
from app.models.models import User, Report, Worker
from app.schemas.schemas import ReportCreate, ReportOut

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/", response_model=list[ReportOut])
def list_reports(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Report).join(Worker).filter(
        Worker.organisation_id == current_user.organisation_id
    )
    if status_filter:
        query = query.filter(Report.status == status_filter)

    return query.order_by(Report.deadline.asc()).all()


@router.post("/", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    worker = db.query(Worker).filter(
        Worker.id == payload.worker_id,
        Worker.organisation_id == current_user.organisation_id,
    ).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    report = Report(**payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.patch("/{report_id}/submit", response_model=ReportOut)
def submit_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).join(Worker).filter(
        Report.id == report_id,
        Worker.organisation_id == current_user.organisation_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = "submitted"
    report.submitted_by = current_user.full_name
    report.submitted_date = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return report
