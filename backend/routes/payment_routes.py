from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user, require_client
import stripe
import os

router = APIRouter(prefix="/api/payments", tags=["Paiements"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_votre_cle_stripe_ici")


@router.post("/create-intent")
def create_payment_intent(
    data: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_client)
):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == data.shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Expédition introuvable")
    if shipment.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorisé")
    if shipment.statut not in [models.ShipmentStatus.OFFRE_ACCEPTEE, models.ShipmentStatus.EN_TRANSIT]:
        raise HTTPException(status_code=400, detail="L'expédition doit avoir une offre acceptée")

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(data.montant * 100),  # En centimes
            currency="xof",  # Franc CFA
            metadata={
                "shipment_id": shipment.id,
                "client_id": current_user.id,
                "camionneur_id": shipment.camionneur_id
            }
        )
        shipment.stripe_payment_intent = intent.id
        db.commit()
        return {"client_secret": intent.client_secret, "payment_intent_id": intent.id}
    except stripe.StripeError as e:
        # Mode simulation si pas de vraie clé Stripe
        return {
            "client_secret": f"simulated_secret_{shipment.id}",
            "payment_intent_id": f"simulated_{shipment.id}",
            "simulation": True,
            "message": "Paiement simulé (configurez STRIPE_SECRET_KEY pour les vrais paiements)"
        }


@router.post("/confirm/{shipment_id}")
def confirm_payment(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_client)
):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Expédition introuvable")
    if shipment.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorisé")

    shipment.paiement_effectue = True
    db.commit()
    return {"message": "Paiement confirmé", "montant": shipment.prix_final}


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role == models.UserRole.CLIENT:
        total = db.query(models.Shipment).filter(models.Shipment.client_id == current_user.id).count()
        livrees = db.query(models.Shipment).filter(
            models.Shipment.client_id == current_user.id,
            models.Shipment.statut == models.ShipmentStatus.LIVRE
        ).count()
        en_cours = db.query(models.Shipment).filter(
            models.Shipment.client_id == current_user.id,
            models.Shipment.statut == models.ShipmentStatus.EN_TRANSIT
        ).count()
        depenses = db.query(models.Shipment).filter(
            models.Shipment.client_id == current_user.id,
            models.Shipment.paiement_effectue == True
        ).all()
        total_depenses = sum(s.prix_final or 0 for s in depenses)

        return {
            "total_expeditions": total,
            "expeditions_livrees": livrees,
            "expeditions_en_cours": en_cours,
            "total_depenses": total_depenses
        }
    else:
        total = db.query(models.Shipment).filter(models.Shipment.camionneur_id == current_user.id).count()
        livrees = db.query(models.Shipment).filter(
            models.Shipment.camionneur_id == current_user.id,
            models.Shipment.statut == models.ShipmentStatus.LIVRE
        ).count()
        en_cours = db.query(models.Shipment).filter(
            models.Shipment.camionneur_id == current_user.id,
            models.Shipment.statut == models.ShipmentStatus.EN_TRANSIT
        ).count()
        gains = db.query(models.Shipment).filter(
            models.Shipment.camionneur_id == current_user.id,
            models.Shipment.paiement_effectue == True
        ).all()
        total_gains = sum(s.prix_final or 0 for s in gains)

        return {
            "total_livraisons": total,
            "livraisons_terminees": livrees,
            "livraisons_en_cours": en_cours,
            "total_gains": total_gains
        }
