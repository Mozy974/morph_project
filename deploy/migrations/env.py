"""
Configuration Alembic pour les migrations du schéma SuperAgent Morph.
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ajouter le répertoire racine au PYTHONPATH pour importer les modèles
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from orchestrator.models import Base

# Alembic Config object
config = context.config

# Configuration du logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata des modèles pour autogenerate
target_metadata = Base.metadata


def get_url():
    """Récupère l'URL de la base de données depuis l'environnement ou le fichier de config."""
    return os.getenv(
        "POSTGRES_URL",
        config.get_main_option("sqlalchemy.url")
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (génère le SQL sans connexion)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connexion directe à la base)."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
