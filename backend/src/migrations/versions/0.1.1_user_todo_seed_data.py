"""Create seed data for users and todos

Revision ID: 0.1.1
Revises: 0.1.0
Create Date: 2021-11-30 21:02:13.637947

"""
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0.1.1"
down_revision = "0.1.0"
branch_labels = None
depends_on = None


def upgrade():
    # We can't currently reflect metadata when using asyncpg and cockroach
    # https://github.com/cockroachdb/cockroach/issues/71908
    # For now, define the tables manually...

    # meta = sa.MetaData(bind=op.get_bind())
    # meta.reflect(only=("users", "todo"))
    # user_table = sa.Table("users", meta)
    # todo_table = sa.Table("todo", meta)

    # table structure copied from 0.1.0 migration
    # TODO: remove this and use reflection once bug is fixed
    user_table = sa.Table(
        "users",
        sa.MetaData(),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("password", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    todo_table = sa.Table(
        "todo",
        sa.MetaData(),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("content", sa.String(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    user1_uuid = uuid.uuid4()  # <- need to save this for Todo creation
    op.bulk_insert(
        user_table,
        [
            {
                "id": user1_uuid,
                "created_at": datetime.now(timezone.utc),
                "name": "user1",
                "password": "pass",
            },
            {
                "id": uuid.uuid4(),
                "created_at": datetime.now(timezone.utc),
                "name": "user2",
                "password": "pass",
            },
            {
                "id": uuid.uuid4(),
                "created_at": datetime.now(timezone.utc),
                "name": "user3",
                "password": "pass",
            },
        ],
    )

    op.bulk_insert(
        todo_table,
        [
            {
                "id": uuid.uuid4(),
                "created_at": datetime.now(timezone.utc),
                "title": "Note 1",
                "content": "My first Note",
                "user_id": user1_uuid,
            },
            {
                "id": uuid.uuid4(),
                "created_at": datetime.now(timezone.utc),
                "title": "Note 2",
                "content": "Edit this Note",
                "user_id": user1_uuid,
            },
            {
                "id": uuid.uuid4(),
                "created_at": datetime.now(timezone.utc),
                "title": "Note 3",
                "content": "Delete this Note",
                "user_id": user1_uuid,
            },
        ],
    )


def downgrade():
    pass
