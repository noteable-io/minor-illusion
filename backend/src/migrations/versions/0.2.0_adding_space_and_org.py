"""adding space and org

Revision ID: 0.2.0
Revises: 0.1.0
Create Date: 2022-01-25 11:55:15.740915

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0.2.0"
down_revision = "0.1.0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organizations_id"), "organizations", ["id"], unique=True)
    op.create_index(
        op.f("ix_organizations_name"), "organizations", ["name"], unique=True
    )
    op.create_table(
        "spaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_spaces_id"), "spaces", ["id"], unique=True)
    op.create_index(op.f("ix_spaces_name"), "spaces", ["name"], unique=True)
    op.create_index(
        op.f("ix_spaces_organization_id"), "spaces", ["organization_id"], unique=False
    )
    op.add_column(
        "todo", sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_index(op.f("ix_todo_space_id"), "todo", ["space_id"], unique=False)
    op.create_foreign_key("fk_todo_spaces", "todo", "spaces", ["space_id"], ["id"])
    op.add_column(
        "users",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_users_organization_id"), "users", ["organization_id"], unique=False
    )
    op.create_foreign_key("fk_users_organizations", "users", "organizations", ["organization_id"], ["id"])


def downgrade():
    raise RuntimeError("cannot be downgraded")
