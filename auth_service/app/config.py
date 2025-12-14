import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()


class Settings:
    # ==========================
    # JWT CONFIGURATION (RS256)
    # ==========================
    JWT_ALGORITHM = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    )

    PRIVATE_KEY_PATH = os.getenv(
        "JWT_PRIVATE_KEY_PATH", "/app/keys/private.pem"
    )
    PUBLIC_KEY_PATH = os.getenv(
        "JWT_PUBLIC_KEY_PATH", "/app/keys/public.pem"
    )

    # ==========================
    # DATABASE
    # ==========================
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "sqlite:///./auth.db"
    )

    # ==========================
    # FERNET ENCRYPTION
    # ==========================
    FERNET_KEY = os.getenv("FERNET_KEY")

    def load_private_key(self) -> str:
        with open(self.PRIVATE_KEY_PATH, "r") as f:
            return f.read()

    def load_public_key(self) -> str:
        with open(self.PUBLIC_KEY_PATH, "r") as f:
            return f.read()

    def get_fernet(self) -> Fernet:
        if not self.FERNET_KEY:
            raise RuntimeError("FERNET_KEY not set")
        return Fernet(self.FERNET_KEY.encode())


settings = Settings()
