import secrets
import string
from datetime import datetime

from sqlmodel import Field, SQLModel


def generate_employee_id():
    """Generate a random 8-digit number string."""
    return "".join(secrets.choice(string.digits) for _ in range(8))


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=generate_employee_id, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
