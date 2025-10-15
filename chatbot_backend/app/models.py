from __future__ import annotations

from .extensions import db


class TimestampMixin:
    """Mixin to add timestamp fields to models."""
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False
    )


class ChatSession(db.Model, TimestampMixin):
    """Represents a chat session which contains multiple messages."""
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)

    # Relationship to messages
    messages = db.relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at.asc()",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} title={self.title!r}>"


class Message(db.Model, TimestampMixin):
    """Represents a single message in a session."""
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role = db.Column(db.String(16), nullable=False)  # 'user' | 'assistant'
    content = db.Column(db.Text, nullable=False)

    # Relationship back to session
    session = db.relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        preview = (self.content[:27] + "...") if len(self.content) > 30 else self.content
        return f"<Message id={self.id} role={self.role} content={preview!r}>"
