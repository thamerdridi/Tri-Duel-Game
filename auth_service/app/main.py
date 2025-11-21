from fastapi import FastAPI
from app.database import Base, engine
from app.auth.routes import router as auth_router

app = FastAPI(title="Tri-Duel Auth Service")

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
