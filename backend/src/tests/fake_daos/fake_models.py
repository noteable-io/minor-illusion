import collections
import uuid
from datetime import datetime, timezone
from typing import Dict, Union
from unittest.mock import MagicMock

import sqlalchemy as sa
from app.models import BaseDAO, TodoDAO, UserDAO
from pydantic import BaseModel


def get_sa_model_defaults(DAO):
    mapper = sa.inspect(DAO)
    defaults = {}
    for c in mapper.columns:
        if c.default:
            if hasattr(c.default.arg, "__wrapped__"):
                defaults[c.name] = c.default.arg.__wrapped__()
            else:
                if isinstance(c.default.arg, sa.sql.functions.now):
                    defaults[c.name] = datetime.now(timezone.utc)
                else:
                    raise Exception(
                        "Unsupported default value: {}".format(c.default.arg)
                    )
    return defaults


class InMemoryDAO:
    # The dao_cls should be a real sqlalchemy model (DAO).
    # What will happen is that we create instances of those
    # real DAOs and store them in memory (cls.CACHE) instead
    # of transacting with a database.
    # Retrieving them is then a matter of pulling from the
    # dictionary instead of reading from a database
    dao_cls: BaseDAO

    # Subclasses will need to create their own CACHE dictionary
    # or will share the same dictionary between classes (not good).
    # Alternatively, have a metaclass create this.
    #
    # A fixture should be in charge of resetting this dictionary
    # in between each test
    CACHE: Dict[uuid.UUID, BaseDAO] = dict()

    # all @classmethod's from BaseDAO should be represented below,
    # but interacting with cls.CACHE instead of a database

    @classmethod
    async def new(cls, session: MagicMock, api_model: Union[BaseDAO, BaseModel, dict]):
        if isinstance(api_model, BaseDAO):
            d = api_model.__dict__.copy()
            d.pop("_sa_instance_state")
            api_model = d
        elif isinstance(api_model, BaseModel):
            api_model = api_model.dict(exclude_unset=True)
        for column, default in get_sa_model_defaults(cls.dao_cls).items():
            api_model.setdefault(column, default)

        model = cls.dao_cls(**api_model)
        cls.CACHE[model.id] = model
        return model

    @classmethod
    async def create(
        cls, session: MagicMock, api_model: Union[BaseDAO, BaseModel, dict]
    ):
        return await cls.new(session, api_model)

    @classmethod
    async def get(cls, session: MagicMock, id: uuid.UUID):
        return cls.CACHE.get(id)

    @classmethod
    async def get_all(cls, session: MagicMock):
        return list(cls.CACHE.values())

    @classmethod
    async def delete(cls, session: MagicMock, id: uuid.UUID):
        # mock returning result.rowcount from database DELETE
        if id in cls.CACHE:
            del cls.CACHE[id]
            return 1
        else:
            return 0


class FakeUserDAO(InMemoryDAO):
    dao_cls = UserDAO
    CACHE = {}

    @classmethod
    async def get_user_by_name(cls, session: MagicMock, name: str):
        matches = [item for item in cls.CACHE.values() if item.name == name]
        if matches:
            return matches[0]
        else:
            return None


class FakeTodoDAO(InMemoryDAO):
    dao_cls = TodoDAO
    CACHE = {}

    @classmethod
    async def get_todos_by_username(cls, session: MagicMock, name: str):
        items = await cls.get_all(session)
        return [item for item in items if item.user.name == name]
