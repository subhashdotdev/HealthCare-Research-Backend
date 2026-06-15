from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from database.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime




class User(Base):
    __tablename__ = 'tbl_users'

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    token = relationship("Token", back_populates="user", cascade='all, delete-orphan')
    search = relationship("Search", back_populates="user", cascade='all, delete-orphan')