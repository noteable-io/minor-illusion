"""Sample data population

Revision ID: 5c5ebec0c9fb
Revises: 128a654019d2
Create Date: 2021-11-04 21:30:20.298038

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c5ebec0c9fb'
down_revision = '128a654019d2'
branch_labels = None
depends_on = None


def upgrade():
    # Ported from app.main's startup hook. This isn't best way, but is progress.

    from app.db import db_session
    from app.models import TodoDAO, UserDAO

    # Seed data
    # create 10 users
    # create a few notes for the first user
    users = []
    for i in range(1, 11):
        name = f"user{i}"
        user = UserDAO(name=name, password="pass")
        users.append(user)

    user1 = users[0]
    todos = [
        TodoDAO(user=user1, title="Note 1", content="My first Note"),
        TodoDAO(user=user1, title="Note 2", content="Edit this Note"),
        TodoDAO(
            user=user1,
            title="Note 3",
            content="So many Notes",
        ),
        TodoDAO(user=user1, title="Note 4", content="Reminder: make more Notes"),
    ]
    with db_session() as session:
        session.add_all(users)
        session.add_all(todos)


def downgrade():
    pass
