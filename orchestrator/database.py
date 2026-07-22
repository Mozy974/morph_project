"""
Configuration de la base de données PostgreSQL — Session factory, engine, helpers.
"""
import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# URL de la base de données (supporte le préfixe db+postgresql:// de Celery)
raw_url = os.getenv("POSTGRES_URL", "postgresql://orchestrator_user:super_secret_password@db:5432/orchestrator_db")

# Nettoyage : Celery utilise db+postgresql://, SQLAlchemy veut postgresql://
if raw_url.startswith("db+"):
    raw_url = raw_url[3:]

DATABASE_URL = raw_url

# Pool configuration pour production
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Générateur de session FastAPI (utilisé comme dépendance).
    Garantit la fermeture de la session après la requête.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_current_org(db: Session, org_id: str) -> None:
    """
    Injecte l'org_id dans la session PostgreSQL pour les politiques RLS.
    À appeler après avoir authentifié l'utilisateur/organisation.
    """
    db.execute(f"SET SESSION app.current_org_id = '{org_id}'")
