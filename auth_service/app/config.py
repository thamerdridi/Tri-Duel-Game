import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    ALGORITHM = "HS256"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth.db")

settings = Settings()
