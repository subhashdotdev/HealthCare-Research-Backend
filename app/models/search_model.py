from sqlalchemy import Column, String, DateTime,ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from database.database import Base
from datetime import datetime



class Search(Base):
    __tablename__ = 'tbl_searches'

    search_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("tbl_users.user_id", ondelete='CASCADE'), nullable=False)
    search_term = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="search", single_parent=True)