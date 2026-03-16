"""
schemas/base.py
───────────────
Shared Pydantic config inherited by all schemas.

Why we use schemas (separate from models):
  - SQLAlchemy models  = how data is STORED in MySQL
  - Pydantic schemas   = how data is TRANSFERRED over HTTP

They look similar but serve different purposes:
  - Models have relationships, lazy loading, DB constraints
  - Schemas have validation rules, field aliases, serialization

Never return a SQLAlchemy model directly from an endpoint.
Always convert to a schema first — this prevents accidentally
leaking fields like password_hash to the frontend.
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime


class Base(BaseModel):
    """
    All schemas inherit from this.
    model_config tells Pydantic how to behave:
      from_attributes=True  → can build schema from a SQLAlchemy object
                               (previously called orm_mode=True in Pydantic v1)
      populate_by_name=True → accept both field name and alias
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TimestampMixin(Base):
    """Adds created_at / updated_at to any response schema."""
    created_at: datetime
    updated_at: datetime
