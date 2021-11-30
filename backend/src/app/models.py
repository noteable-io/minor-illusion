import uuid
from typing import Optional, Union

import sqlalchemy as sa
import sqlalchemy.orm
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_attribute


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
    async def new(cls, session: AsyncSession, api_model: Union[BaseModel, dict]):
        if isinstance(api_model, BaseModel):
            api_model = api_model.dict()

        model = cls(**api_model)
        session.add(model)
        return model

    @classmethod
    async def create(cls, session: AsyncSession, api_model: Union[BaseModel, dict]):
        model = await cls.new(session, api_model)
        await session.flush()
        await session.refresh(model)
        return model

    @classmethod
    async def get(cls, session: AsyncSession, id: uuid.UUID):
        statement = sa.select(cls).where(cls.id == id)
        results = await session.execute(statement)
        return results.scalars().one_or_none()

    @classmethod
    async def get_all(cls, session: AsyncSession):
        statement = sa.select(cls)
        results = await session.execute(statement)
        return results.scalars().all()

    def update(self, api_model: Optional[Union[BaseModel, dict]] = None, **kwargs):
        """Update instance attributes by passing a model, dict, or kwargs to update"""
        if api_model:
            if isinstance(api_model, BaseModel):
                kwargs.update(api_model.dict(exclude_unset=True))
            else:
                kwargs.update(api_model)
        for key, value in kwargs.items():
            set_attribute(self, key, value)

    @classmethod
    async def delete(cls, session: AsyncSession, id: uuid.UUID):
        statement = sa.delete(cls).where(cls.id == id)
        results = await session.execute(statement)
        return results.rowcount


class UserDAO(BaseDAO):
    # special case pluralize tablename to "users" so that
    # it's easier to work with if you're using psql
    __tablename__ = "users"

    name = sa.Column(sa.String, unique=True)
    password = sa.Column(sa.String)
    todos = sa.orm.relationship("TodoDAO", back_populates="user")

    @classmethod
    async def get_user_by_name(cls, session: AsyncSession, name: str):
        statement = sa.select(cls).where(cls.name == name)
        results = await session.execute(statement)
        db_user = results.scalars().one_or_none()
        return db_user


class TodoDAO(BaseDAO):
    __tablename__ = "todo"

    title = sa.Column(sa.String)
    content = sa.Column(sa.String)
    user_id = sa.Column(
        PostgresUUID(as_uuid=True), sa.ForeignKey("users.id"), index=True
    )
    user = sa.orm.relationship("UserDAO", back_populates="todos", lazy="selectin")

    @classmethod
    async def get_todos_by_username(cls, session: AsyncSession, name: str):
        statement = sa.select(cls).join(UserDAO).where(UserDAO.name == name)
        results = await session.execute(statement)
        return results.scalars().all()
