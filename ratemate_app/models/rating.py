from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ratemate_app.db.base import Base



class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    score = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_rating_user_post"),
        UniqueConstraint("user_id", "comment_id", name="uq_rating_user_comment"),
        CheckConstraint("score >= 0 AND score <= 10", name="score_0-10_constraint"),
        CheckConstraint("(post_id IS NOT NULL) <> (comment_id IS NOT NULL)", name="chk_rating_target_one")
    )

    user = relationship("User", back_populates="ratings")
    post = relationship("Post", back_populates="ratings")
    comment = relationship("Comment", back_populates="ratings")