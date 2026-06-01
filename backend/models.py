from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class UserRole(str, enum.Enum):
    CLIENT = "client"
    CAMIONNEUR = "camionneur"


class ShipmentStatus(str, enum.Enum):
    EN_ATTENTE = "en_attente"
    OFFRE_ACCEPTEE = "offre_acceptee"
    EN_TRANSIT = "en_transit"
    LIVRE = "livre"
    ANNULE = "annule"


class OfferStatus(str, enum.Enum):
    EN_ATTENTE = "en_attente"
    ACCEPTEE = "acceptee"
    REFUSEE = "refusee"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    telephone = Column(String, nullable=False)
    mot_de_passe = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    actif = Column(Boolean, default=True)
    date_inscription = Column(DateTime, default=datetime.utcnow)

    # Camionneur specific
    type_camion = Column(String, nullable=True)
    capacite_tonnes = Column(Float, nullable=True)
    numero_plaque = Column(String, nullable=True)
    photo_camion = Column(String, nullable=True)

    shipments = relationship("Shipment", back_populates="client", foreign_keys="Shipment.client_id")
    offers = relationship("Offer", back_populates="camionneur")
    tracking_updates = relationship("TrackingUpdate", back_populates="camionneur")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    camionneur_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    description = Column(Text, nullable=False)
    type_marchandise = Column(String, nullable=False)
    poids_kg = Column(Float, nullable=False)
    volume_m3 = Column(Float, nullable=True)

    adresse_depart = Column(String, nullable=False)
    ville_depart = Column(String, nullable=False)
    adresse_arrivee = Column(String, nullable=False)
    ville_arrivee = Column(String, nullable=False)

    date_souhaitee = Column(String, nullable=False)
    budget_max = Column(Float, nullable=True)

    statut = Column(Enum(ShipmentStatus), default=ShipmentStatus.EN_ATTENTE)
    date_creation = Column(DateTime, default=datetime.utcnow)
    date_livraison = Column(DateTime, nullable=True)

    prix_final = Column(Float, nullable=True)
    paiement_effectue = Column(Boolean, default=False)
    stripe_payment_intent = Column(String, nullable=True)

    client = relationship("User", back_populates="shipments", foreign_keys=[client_id])
    camionneur = relationship("User", foreign_keys=[camionneur_id])
    offers = relationship("Offer", back_populates="shipment")
    tracking_updates = relationship("TrackingUpdate", back_populates="shipment")


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    camionneur_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    prix_propose = Column(Float, nullable=False)
    message = Column(Text, nullable=True)
    delai_jours = Column(Integer, nullable=False)

    statut = Column(Enum(OfferStatus), default=OfferStatus.EN_ATTENTE)
    date_creation = Column(DateTime, default=datetime.utcnow)

    shipment = relationship("Shipment", back_populates="offers")
    camionneur = relationship("User", back_populates="offers")


class TrackingUpdate(Base):
    __tablename__ = "tracking_updates"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    camionneur_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    message = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    shipment = relationship("Shipment", back_populates="tracking_updates")
    camionneur = relationship("User", back_populates="tracking_updates")
