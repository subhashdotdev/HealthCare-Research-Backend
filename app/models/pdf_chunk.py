from sqlalchemy import Column, String, Integer, DateTime,ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from uuid import uuid4
from database.database import Base
from datetime import datetime
from pgvector.sqlalchemy import Vector




class PdfChunk(Base):
    __tablename__ = 'pdf_chunks'

    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete='CASCADE'), nullable=False)
    pdf_path = Column(String(512), nullable=False)
    chunk_text = Column(String, nullable=False)
    embedding = Column(Vector(1536), nullable=False)  
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="chunks")