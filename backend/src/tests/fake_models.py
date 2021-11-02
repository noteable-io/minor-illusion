import uuid
from datetime import datetime
from typing import Union

import sqlalchemy as sa
import sqlalchemy.orm
from app.models import BaseDAO
from pydantic import BaseModel


class InMemoryMeta(type):
    def __new__(cls, name, bases, dct):
        dao = super().__new__(cls, name, bases, dct)
        dao.CACHE = {}
        return dao


class InMemoryDAO(metaclass=InMemoryMeta):
    CACHE: dict
    dao_cls: BaseDAO

    @classmethod
    def new(cls, session: sa.orm.Session, api_model: Union[BaseDAO, BaseModel]):
        if isinstance(api_model, BaseDAO):
            api_model = api_model._attribute_dict
        elif isinstance(api_model, BaseModel):
            api_model = api_model.dict(exclude_unset=True)
        api_model.setdefault("id", uuid.uuid4())
        api_model.setdefault("created_at", datetime.now(datetime.timezone.utc))

        model = cls.dao_cls(**api_model)
        cls.CACHE[model.id] = model
        return model

    @classmethod
    def create(cls, session: sa.orm.Session, api_model: Union[BaseDAO, BaseModel]):
        return cls.new(session, api_model)

    @classmethod
    def get(cls, session: sa.orm.Session, id: uuid.UUID):
        return cls.CACHE.get(id)

    @classmethod
    def get_all(cls, session: sa.orm.Session):
        return list(cls.CACHE.values())


class FakeUserDAO(InMemoryDAO):
    @classmethod
    def get_user_by_name(cls, session: sa.orm.Session, name: str):
        matches = [item for item in cls.CACHE.values() if item["name"] == name]
        if matches:
            return matches[0]
        else:
            return None


class FakeTodoDAO(InMemoryDAO):
    @classmethod
    def get_todos_by_username(cls, session: sa.orm.Session, name: str):
        return [item for item in cls.CACHE.values() if item["user"]["name"] == name]
