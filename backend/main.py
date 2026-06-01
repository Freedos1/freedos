from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os, sys

sys.path.insert(0, os.path.dirname(__file__))

from database import engine
import models
from routes.auth_routes import router as auth_router
from routes.shipment_routes import router as shipment_router
from routes.offer_routes import router as offer_router
from routes.tracking_routes import router as tracking_router
from routes.payment_routes import router as payment_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FREEDOS API",
    description="Plateforme de transport et logistique - Connectez clients et camionneurs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(shipment_router)
app.include_router(offer_router)
app.include_router(tracking_router)
app.include_router(payment_router)

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
static_path = os.path.join(frontend_path, "static")

if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    index = os.path.join(frontend_path, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "FREEDOS API - Transport & Logistique", "docs": "/docs"}


@app.get("/{path:path}", include_in_schema=False)
def serve_spa(path: str):
    # Ne pas intercepter les routes /api/
    if path.startswith("api/") or path.startswith("static/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    index = os.path.join(frontend_path, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "FREEDOS"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
