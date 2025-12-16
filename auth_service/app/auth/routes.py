from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token, create_refresh_token, verify_refresh_token
from app.models import User, RefreshToken, BlacklistedToken
from app.schemas import UserCreate, UserLogin, UserOut, TokenResponse, RefreshTokenRequest
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_token_blacklisted(token: str, db: Session):
    return db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first() is not None

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
@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password.")

    access_token = create_access_token({"sub": user.username, "user_id": user.id, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.username, "user_id": user.id})

    # Store refresh token
    refresh_entry = RefreshToken(token=refresh_token, user_id=user.id, expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7))
    db.add(refresh_entry)
    db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token}


# REFRESH TOKEN
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Check if refresh token exists in DB
    refresh_entry = db.query(RefreshToken).filter(RefreshToken.token == request.refresh_token).first()
    if not refresh_entry or refresh_entry.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=401, detail="Refresh token expired or invalid")

    # Generate new tokens
    access_token = create_access_token({"sub": user.username, "user_id": user.id, "role": user.role})
    new_refresh_token = create_refresh_token({"sub": user.username, "user_id": user.id})

    # Update refresh token in DB
    refresh_entry.token = new_refresh_token
    refresh_entry.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    db.commit()

    return {"access_token": access_token, "refresh_token": new_refresh_token}


# LOGOUT
@router.post("/logout")
def logout(token: str, db: Session = Depends(get_db)):
    if is_token_blacklisted(token, db):
        raise HTTPException(status_code=400, detail="Token already blacklisted")

    blacklisted = BlacklistedToken(token=token)
    db.add(blacklisted)
    db.commit()
    return {"message": "Logged out successfully"}


# VALIDATE TOKEN
@router.get("/validate")
def validate(token: str, db: Session = Depends(get_db)):
    if is_token_blacklisted(token, db):
        raise HTTPException(status_code=401, detail="Token is blacklisted")
    from app.auth.jwt_handler import verify_token
    decoded = verify_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")
    return decoded
