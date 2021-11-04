import uuid
from datetime import datetime
from typing import Union

import sqlalchemy as sa
import sqlalchemy.orm
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


@sa.orm.as_declarative()
class BaseDAO:
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

    @classmethod
    def new(cls, session: sa.orm.Session, api_model: Union[BaseModel, dict]):
        if isinstance(api_model, BaseModel):
            api_model = api_model.dict()

        model = cls(**api_model)
        session.add(model)
        return model

    @classmethod
    def create(cls, session: sa.orm.Session, api_model: Union[BaseModel, dict]):
        model = cls.new(session, api_model)
        session.flush()
        session.refresh(model)
        return model

    @classmethod
    def get(cls, session: sa.orm.Session, id: uuid.UUID):
        statement = sa.select(cls).where(cls.id == id)
        results = session.execute(statement)
        return results.scalars().one_or_none()

    @classmethod
    def get_all(cls, session: sa.orm.Session):
        statement = sa.select(cls)
        results = session.execute(statement)
        return results.scalars().all()

    @classmethod
    def delete(cls, session: sa.orm.Session, id: uuid.UUID):
        statement = sa.delete(cls).where(cls.id == id)
        results = session.execute(statement)
        return results.rowcount


class UserDAO(BaseDAO):
    __tablename__ = "users"

    name = sa.Column(sa.String)
    password = sa.Column(sa.String)
    todos = sa.orm.relationship("TodoDAO", back_populates="user")

    @classmethod
    def get_user_by_name(cls, session: sa.orm.Session, name: str):
        statement = sa.select(cls).where(cls.name == name)
        results = session.execute(statement)
        db_user = results.scalars().one_or_none()
        return db_user


class TodoDAO(BaseDAO):
    __tablename__ = "todo"

    title = sa.Column(sa.String)
    content = sa.Column(sa.String)
    user_id = sa.Column(PostgresUUID(as_uuid=True), sa.ForeignKey("users.id"), index=True)
    user = sa.orm.relationship("UserDAO", back_populates="todos", lazy="joined")

    @classmethod
    def get_todos_by_username(cls, session: sa.orm.Session, name: str):
        statement = sa.select(cls).join(UserDAO).where(UserDAO.name == name)
        results = session.execute(statement)
        return results.scalars().all()
