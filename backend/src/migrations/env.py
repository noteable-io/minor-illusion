from logging.config import fileConfig

from alembic import context

# All app's models live in app.models, so nothing else to import.
from app.models import BaseDAO
from app.settings import get_settings
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# Override the config option from ini file with what codebase knows.
config.set_main_option("sqlalchemy.url", get_settings().DB_DSN)


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = BaseDAO.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# recipe from https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # "transactions_per_migration" may or may not be necessary as alembic
        # upgrades past 1.5.0
        # see https://alembic.sqlalchemy.org/en/latest/changelog.html#change-3374635e9b84c495d2ede3c978cd57e6
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=True,
            as_sql=False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
