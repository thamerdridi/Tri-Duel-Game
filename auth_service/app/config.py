import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    ALGORITHM = "HS256"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth.db")
    PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "https://player_service:8002")
    SERVICE_API_KEY = os.getenv("PLAYER_SERVICE_API_KEY", "default-api-key")
    CA_BUNDLE_PATH = os.getenv("CA_BUNDLE_PATH", "/certs/ca/ca.crt")

settings = Settings()
