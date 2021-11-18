import collections
import uuid
from datetime import datetime, timezone
from typing import Dict, Union
from unittest.mock import Mock

from app.models import BaseDAO, TodoDAO, UserDAO
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


class InMemoryDAO:
    CACHE: Dict[Mock, Dict[PostgresUUID, BaseDAO]] = collections.defaultdict(dict)
    dao_cls: BaseDAO

    @classmethod
    def new(cls, mock_session: Mock, api_model: Union[BaseDAO, BaseModel, dict]):
        if isinstance(api_model, BaseDAO):
            d = api_model.__dict__.copy()
            d.pop("_sa_instance_state")
            api_model = d
        elif isinstance(api_model, BaseModel):
            api_model = api_model.dict(exclude_unset=True)
        api_model.setdefault("id", uuid.uuid4())
        api_model.setdefault("created_at", datetime.now(timezone.utc))

        model = cls.dao_cls(**api_model)
        cls.CACHE[model.id] = model
        return model

    @classmethod
    def create(cls, mock_session: Mock, api_model: Union[BaseDAO, BaseModel]):
        return cls.new(session, api_model)

    @classmethod
    def get(cls, mock_session: Mock, id: uuid.UUID):
        return cls.CACHE.get(id)

    @classmethod
    def get_all(cls, mock_session: Mock):
        return list(cls.CACHE.values())

    @classmethod
    def delete(cls, mock_session: Mock, id: uuid.UUID):
        if id in cls.CACHE:
            del cls.CACHE[id]
            return 1
        else:
            return 0


class FakeUserDAO(InMemoryDAO):
    dao_cls = UserDAO

    @classmethod
    def get_user_by_name(cls, session: Session, name: str):
        matches = [item for item in cls.CACHE.values() if item.name == name]
        if matches:
            return matches[0]
        else:
            return None


class FakeTodoDAO(InMemoryDAO):
    dao_cls = TodoDAO

    @classmethod
    def get_todos_by_username(cls, session: Session, name: str):
        return [item for item in cls.CACHE.values() if item.user.name == name]

    @classmethod
    def update_by_id(cls, session: Session, id: uuid.UUID, **values):
        item = cls.get(session, id)
        if not item:
            return
        item.__dict__.update(values)
        return item
