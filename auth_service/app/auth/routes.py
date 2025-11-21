from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.models import User
from app.schemas import UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# REGISTER NEW USER
@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):

    user_exists = db.query(User).filter(User.username == user.username).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Username already taken.")

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# LOGIN USER
@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password.")

    token = create_access_token({"sub": user.username, "user_id": user.id})

    return {"access_token": token, "token_type": "bearer"}


# VALIDATE TOKEN
@router.get("/validate")
def validate(token: str):
    from app.auth.jwt_handler import verify_token
    decoded = verify_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")
    return decoded
