import uuid
from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


@sa.orm.as_declarative()
class Base:
    id = sa.Column(
        PostgresUUID(as_uuid=True),
        index=True,
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    created_at = sa.Column(
        sa.TIMESTAMP(timezone=True), default=sa.func.now(), nullable=False
    )


class User(Base):
    __tablename__ = "user"

    name = sa.Column(sa.String)
    password = sa.Column(sa.String)
    todos = sa.orm.relationship("Todo", back_populates="user")


class Todo(Base):
    __tablename__ = "todo"

    title = sa.Column(sa.String)
    content = sa.Column(sa.String)
    user_id = sa.Column(PostgresUUID(as_uuid=True), sa.ForeignKey("user.id"))
    user = sa.orm.relationship("User", back_populates="todos", lazy="joined")
