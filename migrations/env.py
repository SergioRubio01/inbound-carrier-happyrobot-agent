import os
import sys

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from src.config.settings import settings
from src.infrastructure.database.base import Base

# Import all models to ensure they are registered with SQLAlchemy
from src.infrastructure.database.models import *  # noqa: F401,F403

# Load environment variables from .env file
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


# Define all database URLs
databases = {
    "postgres": settings.get_sync_database_url,
}

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def process_revision_directives(context, revision, directives):
    # Remove the empty operations check for initial migration
    """if config.cmd_opts and config.cmd_opts.autogenerate:
    script = directives[0]
    if script.upgrade_ops.is_empty():
        directives[:] = []"""

    # Handle multiple databases
    if directives and hasattr(directives[0], "upgrade_ops"):
        # Handle single database case
        if not directives[0].upgrade_ops_list:
            ops_list = [directives[0].upgrade_ops]
        else:
            ops_list = directives[0].upgrade_ops_list

        for ops in ops_list:
            for op in ops.ops:
                # Handle foreign key constraints
                if hasattr(op, "constraint_name") and op.constraint_name is None:
                    if hasattr(op, "source_table") and hasattr(op, "referent_table"):
                        op.constraint_name = f"fk_{op.source_table}_{op.referent_table}"
                    elif hasattr(op, "table_name") and hasattr(op, "columns"):
                        # Handle other constraints (unique, check, etc.)
                        cols = (
                            "_".join(col.name for col in op.columns)
                            if hasattr(op, "columns")
                            else "constraint"
                        )
                        op.constraint_name = f"{op.table_name}_{cols}_fkey"


def run_migrations_for_db(db_url):
    # Override sqlalchemy.url in alembic.ini
    # Escape % characters for configparser by doubling them
    escaped_url = db_url.replace('%', '%%')
    config.set_main_option("sqlalchemy.url", escaped_url)

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = db_url
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


def run_migrations():
    # Run migrations for each database
    for db_name, db_url in databases.items():
        print(f"Running migrations for {db_name} database...")
        run_migrations_for_db(db_url)
        print(f"Completed migrations for {db_name} database.")


if context.is_offline_mode():
    print("Offline mode not supported for multiple databases")
else:
    run_migrations()
