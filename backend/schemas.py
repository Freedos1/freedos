from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import UserRole, ShipmentStatus, OfferStatus


class UserRegister(BaseModel):
    nom: str
    prenom: str
    email: str
    telephone: str
    mot_de_passe: str
    role: UserRole
    type_camion: Optional[str] = None
    capacite_tonnes: Optional[float] = None
    numero_plaque: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    mot_de_passe: str


class UserOut(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    telephone: str
    role: UserRole
    type_camion: Optional[str] = None
    capacite_tonnes: Optional[float] = None
    numero_plaque: Optional[str] = None
    date_inscription: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class ShipmentCreate(BaseModel):
    description: str
    type_marchandise: str
    poids_kg: float
    volume_m3: Optional[float] = None
    adresse_depart: str
    ville_depart: str
    adresse_arrivee: str
    ville_arrivee: str
    date_souhaitee: str
    budget_max: Optional[float] = None


class ShipmentOut(BaseModel):
    id: int
    client_id: int
    camionneur_id: Optional[int] = None
    description: str
    type_marchandise: str
    poids_kg: float
    volume_m3: Optional[float] = None
    adresse_depart: str
    ville_depart: str
    adresse_arrivee: str
    ville_arrivee: str
    date_souhaitee: str
    budget_max: Optional[float] = None
    statut: ShipmentStatus
    date_creation: datetime
    prix_final: Optional[float] = None
    paiement_effectue: bool
    client: Optional[UserOut] = None
    camionneur: Optional[UserOut] = None
    offers: List["OfferOut"] = []

    class Config:
        from_attributes = True


class OfferCreate(BaseModel):
    prix_propose: float
    message: Optional[str] = None
    delai_jours: int


class OfferOut(BaseModel):
    id: int
    shipment_id: int
    camionneur_id: int
    prix_propose: float
    message: Optional[str] = None
    delai_jours: int
    statut: OfferStatus
    date_creation: datetime
    camionneur: Optional[UserOut] = None

    class Config:
        from_attributes = True


class TrackingUpdate(BaseModel):
    latitude: float
    longitude: float
    message: Optional[str] = None


class TrackingOut(BaseModel):
    id: int
    shipment_id: int
    latitude: float
    longitude: float
    message: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    shipment_id: int
    montant: float


ShipmentOut.model_rebuild()
