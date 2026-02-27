from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.deps import get_current_user
from app.models.models import User, Alert, Worker
from app.schemas.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=list[AlertOut])
def list_alerts(
    severity: str | None = None,
    resolved: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Alert).join(Worker).filter(
        Worker.organisation_id == current_user.organisation_id,
        Alert.is_resolved == resolved,
    )
    if severity:
        query = query.filter(Alert.severity == severity)

    return query.order_by(Alert.created_at.desc()).all()


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(Alert).join(Worker).filter(
        Alert.id == alert_id,
        Worker.organisation_id == current_user.organisation_id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_resolved = True
    db.commit()
    db.refresh(alert)
    return alert
