import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token, verify_token
from app.models import User
from app.schemas import UserCreate, UserLogin, UserOut
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
PASSWORD_REGEX = re.compile(
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}$"
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================
# REGISTER
# ==========================
@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED
)
def register(user: UserCreate, db: Session = Depends(get_db)):

    if not USERNAME_REGEX.match(user.username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-20 characters (letters, numbers, underscore)"
        )

    if not PASSWORD_REGEX.match(user.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be 8+ chars, upper, lower, number"
        )

    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")

    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=409, detail="Email already exists")

    fernet = settings.get_fernet()
    encrypted_email = fernet.encrypt(user.email.encode()).decode()

    new_user = User(
        username=user.username,
        email=encrypted_email,
        hashed_password=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserOut(
        id=new_user.id,
        username=new_user.username,
        email=user.email  # decrypted response
    )


# ==========================
# LOGIN
# ==========================
@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.username == credentials.username
    ).first()

    if not user or not verify_password(
        credentials.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token(
        subject=user.username,
        user_id=user.id
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ==========================
# TOKEN VALIDATION
# ==========================
@router.get("/validate")
def validate_token(token: str):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return payload
