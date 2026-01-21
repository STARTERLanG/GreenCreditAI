from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"  # type: ignore

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str | None = Field(default=None)
    history: str = Field(default="[]", description="JSON serialized chat history")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
