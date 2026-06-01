from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models, schemas
from auth import get_current_user, require_client, require_camionneur

router = APIRouter(prefix="/api/shipments", tags=["Expéditions"])


@router.post("", response_model=schemas.ShipmentOut)
def create_shipment(
    data: schemas.ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_client)
):
    shipment = models.Shipment(client_id=current_user.id, **data.model_dump())
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


@router.get("", response_model=List[schemas.ShipmentOut])
def list_shipments(
    statut: Optional[str] = None,
    ville_depart: Optional[str] = None,
    ville_arrivee: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Shipment)

    if current_user.role == models.UserRole.CLIENT:
        query = query.filter(models.Shipment.client_id == current_user.id)
    else:
        # Camionneurs voient les expéditions en attente + leurs expéditions assignées
        if not statut or statut == "en_attente":
            query = query.filter(
                (models.Shipment.statut == models.ShipmentStatus.EN_ATTENTE) |
                (models.Shipment.camionneur_id == current_user.id)
            )
        else:
            query = query.filter(models.Shipment.camionneur_id == current_user.id)

    if statut:
        query = query.filter(models.Shipment.statut == statut)
    if ville_depart:
        query = query.filter(models.Shipment.ville_depart.ilike(f"%{ville_depart}%"))
    if ville_arrivee:
        query = query.filter(models.Shipment.ville_arrivee.ilike(f"%{ville_arrivee}%"))

    return query.order_by(models.Shipment.date_creation.desc()).all()


@router.get("/{shipment_id}", response_model=schemas.ShipmentOut)
def get_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Expédition introuvable")
    return shipment


@router.put("/{shipment_id}/statut")
def update_shipment_status(
    shipment_id: int,
    statut: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Expédition introuvable")

    if current_user.role == models.UserRole.CAMIONNEUR and shipment.camionneur_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorisé")

    shipment.statut = statut
    if statut == models.ShipmentStatus.LIVRE:
        from datetime import datetime
        shipment.date_livraison = datetime.utcnow()

    db.commit()
    return {"message": "Statut mis à jour", "statut": statut}
