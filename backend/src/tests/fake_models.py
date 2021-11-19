import collections
import uuid
from datetime import datetime, timezone
from typing import Dict, Union
from unittest.mock import Mock

from app.models import BaseDAO, TodoDAO, UserDAO
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


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
    # In order to sort-of simulate transactional rollback and per-test
    # isolation, the structure is {mock_db_session: {model.id: model}}
    CACHE: Dict[Mock, Dict[PostgresUUID, BaseDAO]] = collections.defaultdict(dict)

    # all @classmethod's from BaseDAO should be represented below,
    # but interacting with cls.CACHE instead of a database

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
        cls.CACHE[mock_session][model.id] = model
        return model

    @classmethod
    def create(cls, mock_session: Mock, api_model: Union[BaseDAO, BaseModel]):
        return cls.new(mock_session, api_model)

    @classmethod
    def get(cls, mock_session: Mock, id: uuid.UUID):
        return cls.CACHE[mock_session].get(id)

    @classmethod
    def get_all(cls, mock_session: Mock):
        return list(cls.CACHE[mock_session].values())

    @classmethod
    def delete(cls, mock_session: Mock, id: uuid.UUID):
        # mock returning result.rowcount from database DELETE
        if id in cls.CACHE[mock_session]:
            del cls.CACHE[mock_session][id]
            return 1
        else:
            return 0


class FakeUserDAO(InMemoryDAO):
    dao_cls = UserDAO
    CACHE = collections.defaultdict(dict)

    @classmethod
    def get_user_by_name(cls, mock_session: Mock, name: str):
        matches = [
            item for item in cls.CACHE[mock_session].values() if item.name == name
        ]
        if matches:
            return matches[0]
        else:
            return None


class FakeTodoDAO(InMemoryDAO):
    dao_cls = TodoDAO
    CACHE = collections.defaultdict(dict)

    @classmethod
    def get_todos_by_username(cls, mock_session: Mock, name: str):
        return [item for item in cls.get_all(mock_session) if item.user.name == name]

    @classmethod
    def update_by_id(cls, mock_session: Mock, id: uuid.UUID, **values):
        item = cls.get(mock_session, id)
        if not item:
            return
        item.__dict__.update(values)
        return item
