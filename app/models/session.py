from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from database.database import Base
from datetime import datetime




class Session(Base):
    __tablename__ = 'sessions'

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pdf_path = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("PdfChunk", back_populates="session", cascade='all, delete-orphan')