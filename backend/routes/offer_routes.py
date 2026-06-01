from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
from auth import get_current_user, require_client, require_camionneur

router = APIRouter(prefix="/api/offers", tags=["Offres"])


@router.post("/shipment/{shipment_id}", response_model=schemas.OfferOut)
def create_offer(
    shipment_id: int,
    data: schemas.OfferCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_camionneur)
):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Expédition introuvable")
    if shipment.statut != models.ShipmentStatus.EN_ATTENTE:
        raise HTTPException(status_code=400, detail="Cette expédition n'accepte plus d'offres")

    existing = db.query(models.Offer).filter(
        models.Offer.shipment_id == shipment_id,
        models.Offer.camionneur_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vous avez déjà soumis une offre")

    offer = models.Offer(
        shipment_id=shipment_id,
        camionneur_id=current_user.id,
        **data.model_dump()
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.get("/shipment/{shipment_id}", response_model=List[schemas.OfferOut])
def get_shipment_offers(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Offer).filter(models.Offer.shipment_id == shipment_id).all()


@router.post("/{offer_id}/accept")
def accept_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_client)
):
    offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offre introuvable")

    shipment = db.query(models.Shipment).filter(models.Shipment.id == offer.shipment_id).first()
    if shipment.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorisé")

    # Accepter cette offre
    offer.statut = models.OfferStatus.ACCEPTEE
    shipment.camionneur_id = offer.camionneur_id
    shipment.prix_final = offer.prix_propose
    shipment.statut = models.ShipmentStatus.OFFRE_ACCEPTEE

    # Refuser les autres offres
    db.query(models.Offer).filter(
        models.Offer.shipment_id == offer.shipment_id,
        models.Offer.id != offer_id
    ).update({"statut": models.OfferStatus.REFUSEE})

    db.commit()
    return {"message": "Offre acceptée avec succès", "prix_final": offer.prix_propose}


@router.post("/{offer_id}/refuse")
def refuse_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_client)
):
    offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offre introuvable")

    offer.statut = models.OfferStatus.REFUSEE
    db.commit()
    return {"message": "Offre refusée"}
