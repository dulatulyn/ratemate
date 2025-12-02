from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ratemate_app.db.base import Base

class Lowkey(Base):
    __tablename__ = "lowkeys"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=True)
    media_url = Column(String, nullable=True)
    media_type = Column(String, nullable=True)
    visibility = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("visibility IN ('public','followers')", name="lowkey_visibility_enum"),
    )

    owner = relationship("User")
    views = relationship("LowkeyView", back_populates="lowkey", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="lowkey", cascade="all, delete-orphan")

class LowkeyView(Base):
    __tablename__ = "lowkey_views"

    id = Column(Integer, primary_key=True, index=True)
    lowkey_id = Column(Integer, ForeignKey("lowkeys.id", ondelete="CASCADE"), nullable=False, index=True)
    viewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("lowkey_id", "viewer_id", name="uq_lowkey_view_unique"),
    )

    lowkey = relationship("Lowkey", back_populates="views")
    viewer = relationship("User")

    