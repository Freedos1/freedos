from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post("/register", response_model=schemas.TokenResponse)
def register(data: schemas.UserRegister, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    if data.role == models.UserRole.CAMIONNEUR:
        if not data.type_camion or not data.numero_plaque:
            raise HTTPException(status_code=400, detail="Informations du camion requises")

    user = models.User(
        nom=data.nom,
        prenom=data.prenom,
        email=data.email,
        telephone=data.telephone,
        mot_de_passe=get_password_hash(data.mot_de_passe),
        role=data.role,
        type_camion=data.type_camion,
        capacite_tonnes=data.capacite_tonnes,
        numero_plaque=data.numero_plaque,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.mot_de_passe, user.mot_de_passe):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user
