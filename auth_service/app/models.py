from sqlalchemy import Column, Integer, String
from app.database import Base
from app.config import settings

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    _email = Column("email", String)
    hashed_password = Column(String)

    @property
    def email(self):
        return settings.get_fernet().decrypt(self._email.encode()).decode()

    @email.setter
    def email(self, value):
        self._email = settings.get_fernet().encrypt(value.encode()).decode()
