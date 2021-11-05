"""Sample data population

Revision ID: 5c5ebec0c9fb
Revises: 128a654019d2
Create Date: 2021-11-04 21:30:20.298038

"""

# revision identifiers, used by Alembic.
revision = '5c5ebec0c9fb'
down_revision = '128a654019d2'
branch_labels = None
depends_on = None


def upgrade():
    from app.create_seed_data import create_seed_data

    create_seed_data()


def downgrade():
    pass
