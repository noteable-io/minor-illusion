from contextlib import contextmanager

import sqlalchemy as sa
import sqlalchemy.orm

from app.settings import settings

engine = sa.create_engine(settings.DB_DSN)

LocalSession = sa.orm.sessionmaker(engine, expire_on_commit=False)


@contextmanager
def db_session():
    session = LocalSession()
    try:
        yield session
        session.commit()
    finally:
        session.close()
