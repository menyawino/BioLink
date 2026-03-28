"""
SQLAlchemy User model for authentication and authorization.
"""

from datetime import UTC, datetime
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    Integer,
)
from sqlalchemy.dialects.postgresql import ARRAY
from app.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="viewer")  # admin, researcher, viewer
    scopes = Column(ARRAY(String), nullable=False, default=list)
    disabled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"
