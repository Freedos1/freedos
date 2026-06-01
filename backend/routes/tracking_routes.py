from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict
from database import get_db, SessionLocal
import models, schemas
from auth import get_current_user, require_camionneur
import json

router = APIRouter(prefix="/api/tracking", tags=["Suivi"])

# Gestionnaire de connexions WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, shipment_id: int):
        await websocket.accept()
        if shipment_id not in self.active_connections:
            self.active_connections[shipment_id] = []
        self.active_connections[shipment_id].append(websocket)

    def disconnect(self, websocket: WebSocket, shipment_id: int):
        if shipment_id in self.active_connections:
            self.active_connections[shipment_id].remove(websocket)

    async def broadcast(self, shipment_id: int, data: dict):
        if shipment_id in self.active_connections:
            for connection in self.active_connections[shipment_id]:
                try:
                    await connection.send_text(json.dumps(data))
                except Exception:
                    pass


manager = ConnectionManager()


@router.post("/update/{shipment_id}", response_model=schemas.TrackingOut)
def update_location(
    shipment_id: int,
    data: schemas.TrackingUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_camionneur)
):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Expédition introuvable")
    if shipment.camionneur_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorisé")

    tracking = models.TrackingUpdate(
        shipment_id=shipment_id,
        camionneur_id=current_user.id,
        latitude=data.latitude,
        longitude=data.longitude,
        message=data.message
    )
    db.add(tracking)

    if shipment.statut == models.ShipmentStatus.OFFRE_ACCEPTEE:
        shipment.statut = models.ShipmentStatus.EN_TRANSIT

    db.commit()
    db.refresh(tracking)
    return tracking


@router.get("/history/{shipment_id}", response_model=List[schemas.TrackingOut])
def get_tracking_history(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.TrackingUpdate).filter(
        models.TrackingUpdate.shipment_id == shipment_id
    ).order_by(models.TrackingUpdate.timestamp.desc()).limit(50).all()


@router.websocket("/ws/{shipment_id}")
async def websocket_tracking(websocket: WebSocket, shipment_id: int):
    await manager.connect(websocket, shipment_id)
    db = SessionLocal()
    try:
        # Envoyer le dernier point connu
        last = db.query(models.TrackingUpdate).filter(
            models.TrackingUpdate.shipment_id == shipment_id
        ).order_by(models.TrackingUpdate.timestamp.desc()).first()

        if last:
            await websocket.send_text(json.dumps({
                "latitude": last.latitude,
                "longitude": last.longitude,
                "message": last.message,
                "timestamp": str(last.timestamp)
            }))

        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            # Sauvegarder la mise à jour
            tracking = models.TrackingUpdate(
                shipment_id=shipment_id,
                camionneur_id=payload.get("camionneur_id", 0),
                latitude=payload["latitude"],
                longitude=payload["longitude"],
                message=payload.get("message")
            )
            db.add(tracking)
            db.commit()

            # Diffuser à tous les abonnés
            await manager.broadcast(shipment_id, {
                "latitude": payload["latitude"],
                "longitude": payload["longitude"],
                "message": payload.get("message"),
                "timestamp": str(tracking.timestamp)
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, shipment_id)
    finally:
        db.close()
