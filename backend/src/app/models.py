import uuid
from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlmodel import Field, Relationship, SQLModel


class Base(SQLModel):
    id: uuid.UUID = Field(
        sa_column=sa.Column(PostgresUUID(as_uuid=True), index=True, primary_key=True),
        default_factory=uuid.uuid4,
    )
    created_at: datetime = Field(
        sa_column=sa.Column(sa.TIMESTAMP(timezone=True), nullable=False),
        default_factory=datetime.now,
    )


class User(Base, table=True):
    name: str
    password: str
    todos: List["Todo"] = Relationship(back_populates="user")


class Todo(Base, table=True):
    title: str
    content: str
    user_id: uuid.UUID = Field(default=None, foreign_key="user.id")
    user: User = Relationship(back_populates="todos")
