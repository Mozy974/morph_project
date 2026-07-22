#!/usr/bin/env python3
"""
Script de migration des données JSON existantes vers PostgreSQL.
Migration complète et réversible :
  1. long_term_skills.json → table skills
  2. Checkpoints (fichiers JSON) → table checkpoints
  3. Création d'une organisation par défaut + utilisateur admin

Usage:
    python scripts/migrate_json_to_db.py              # Migration complète
    python scripts/migrate_json_to_db.py --dry-run     # Simulation sans écriture
    python scripts/migrate_json_to_db.py --rollback    # Annulation (suppression des données migrées)
"""
import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Ajout du projet au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator.models import (
    Organization, User, Skill, Checkpoint, Job, AuditLog, HumanValidation, ApiKey
)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# --- Configuration ---
SKILLS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "orchestrator", "memory", "long_term_skills.json"
)
CHECKPOINTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "orchestrator", "memory", "checkpoints"
)
DEFAULT_ORG_NAME = "Default Organization"
DEFAULT_ORG_SLUG = "default"
DEFAULT_ADMIN_EMAIL = "admin@morph.local"
DEFAULT_ADMIN_NAME = "Admin Morph"

POSTGRES_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql://orchestrator_user:super_secret_password@localhost:5432/orchestrator_db"
)


def get_session() -> Session:
    """Crée une session SQLAlchemy."""
    engine = create_engine(POSTGRES_URL)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def get_or_create_default_org(session: Session, dry_run: bool = False) -> Organization:
    """Récupère ou crée l'organisation par défaut."""
    org = session.query(Organization).filter_by(slug=DEFAULT_ORG_SLUG).first()
    if org:
        print(f"  ℹ️ Organisation existante : {org.name} ({org.org_id})")
        return org

    if dry_run:
        print(f"  🔷 [DRY-RUN] Créerait l'organisation : {DEFAULT_ORG_NAME}")
        return Organization(
            org_id=uuid.uuid4(),
            name=DEFAULT_ORG_NAME,
            slug=DEFAULT_ORG_SLUG,
            api_key_hash="migration_placeholder",
        )

    org = Organization(
        name=DEFAULT_ORG_NAME,
        slug=DEFAULT_ORG_SLUG,
        api_key_hash=hashlib.sha256(b"migration_placeholder").hexdigest(),
    )
    session.add(org)
    session.flush()
    print(f"  ✅ Organisation créée : {org.name} ({org.org_id})")
    return org


def get_or_create_admin_user(session: Session, org_id: uuid.UUID, dry_run: bool = False) -> User:
    """Récupère ou crée l'utilisateur admin par défaut."""
    user = session.query(User).filter_by(org_id=org_id, email=DEFAULT_ADMIN_EMAIL).first()
    if user:
        print(f"  ℹ️ Utilisateur existant : {user.display_name} ({user.user_id})")
        return user

    if dry_run:
        print(f"  🔷 [DRY-RUN] Créerait l'utilisateur : {DEFAULT_ADMIN_EMAIL}")
        return User(
            user_id=uuid.uuid4(),
            org_id=org_id,
            email=DEFAULT_ADMIN_EMAIL,
            display_name=DEFAULT_ADMIN_NAME,
            role="admin",
        )

    user = User(
        org_id=org_id,
        email=DEFAULT_ADMIN_EMAIL,
        display_name=DEFAULT_ADMIN_NAME,
        role="admin",
    )
    session.add(user)
    session.flush()
    print(f"  ✅ Utilisateur admin créé : {user.display_name} ({user.user_id})")
    return user


def migrate_skills(session: Session, org_id: uuid.UUID, user_id: uuid.UUID,
                   dry_run: bool = False) -> Dict[str, Any]:
    """Migre long_term_skills.json vers la table skills."""
    if not os.path.exists(SKILLS_FILE):
        return {"status": "skipped", "reason": "Fichier long_term_skills.json introuvable"}

    with open(SKILLS_FILE, "r", encoding="utf-8") as f:
        skills_data = json.load(f)

    if not isinstance(skills_data, list):
        return {"status": "error", "reason": "Format JSON invalide : liste attendue"}

    print(f"  📦 {len(skills_data)} skills trouvés dans le fichier JSON")

    imported = 0
    skipped = 0

    for skill_entry in skills_data:
        skill_id_str = skill_entry.get("id", "")
        if not skill_id_str:
            skipped += 1
            continue

        # Vérifier si déjà importé (par l'ID original stocké dans sha256_hash)
        existing = session.query(Skill).filter_by(sha256_hash=skill_id_str).first()
        if existing:
            skipped += 1
            continue

        status_map = {
            "PENDING_APPROVAL": "PENDING_APPROVAL",
            "APPROVED": "APPROVED",
            "REJECTED": "REJECTED",
        }
        status = status_map.get(skill_entry.get("status", "PENDING_APPROVAL"), "PENDING_APPROVAL")

        if dry_run:
            print(f"    🔷 [DRY-RUN] Importerait : {skill_entry.get('sujet_cle', 'Sans nom')[:60]}...")
            imported += 1
            continue

        skill = Skill(
            org_id=org_id,
            status=status,
            subject_key=skill_entry.get("sujet_cle", "Skill Sans Nom"),
            directive_text=skill_entry.get("directive_corrective", ""),
            error_context=skill_entry.get("contexte_erreur", ""),
            keywords_json=skill_entry.get("mots_cles", []),
            sha256_hash=skill_id_str,  # ID original conservé pour traçabilité
            approved_by=user_id if status == "APPROVED" else None,
            approved_at=datetime.now(timezone.utc).replace(tzinfo=None) if status == "APPROVED" else None,
        )
        session.add(skill)
        imported += 1

    if not dry_run:
        session.flush()

    return {
        "status": "success",
        "imported": imported,
        "skipped": skipped,
        "total": len(skills_data),
    }


def migrate_checkpoints(session: Session, org_id: uuid.UUID, dry_run: bool = False) -> Dict[str, Any]:
    """Migre les checkpoints depuis les fichiers JSON vers la table checkpoints."""
    if not os.path.isdir(CHECKPOINTS_DIR):
        return {"status": "skipped", "reason": "Répertoire checkpoints introuvable"}

    checkpoint_files = [f for f in os.listdir(CHECKPOINTS_DIR) if f.endswith(".json")]
    print(f"  📦 {len(checkpoint_files)} fichiers checkpoint trouvés")

    imported = 0
    skipped = 0

    for filename in checkpoint_files:
        job_id_str = filename.replace(".json", "")

        # Valider que c'est un UUID valide
        try:
            job_uuid = uuid.UUID(job_id_str)
        except ValueError:
            skipped += 1
            continue

        filepath = os.path.join(CHECKPOINTS_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            skipped += 1
            continue

        if dry_run:
            print(f"    🔷 [DRY-RUN] Importerait checkpoint : {job_id_str}")
            imported += 1
            continue

        # Créer un job minimal si nécessaire
        job = session.query(Job).filter_by(job_id=job_uuid).first()
        if not job:
            job = Job(
                job_id=job_uuid,
                org_id=org_id,
                task_text=state_data.get("task", "Migrated checkpoint"),
                status=state_data.get("status", "IN_PROGRESS"),
                last_node=state_data.get("last_completed_node", "START"),
                retry_count=state_data.get("retry_count", 0),
            )
            session.add(job)
            session.flush()

        # Vérifier si le checkpoint existe déjà
        existing = session.query(Checkpoint).filter_by(job_id=job_uuid).first()
        if existing:
            skipped += 1
            continue

        checkpoint = Checkpoint(
            job_id=job_uuid,
            org_id=org_id,
            state_blob=state_data,
            last_node=state_data.get("last_completed_node", "START"),
            retry_count=state_data.get("retry_count", 0),
        )
        session.add(checkpoint)
        imported += 1

    if not dry_run:
        session.flush()

    return {
        "status": "success",
        "imported": imported,
        "skipped": skipped,
        "total": len(checkpoint_files),
    }


def rollback(session: Session) -> Dict[str, Any]:
    """Annule la migration : supprime toutes les données migrées."""
    print("\n⚠️  ROLLBACK : Suppression des données migrées...")

    counts = {}
    for table_name in ["human_validations", "audit_logs", "checkpoints", "skills", "api_keys", "jobs", "projects", "users", "organizations"]:
        result = session.execute(text(f"DELETE FROM {table_name}"))
        counts[table_name] = result.rowcount

    session.commit()

    print("  ✅ Rollback terminé :")
    for table, count in counts.items():
        if count > 0:
            print(f"    - {table}: {count} lignes supprimées")
    return counts


def main():
    parser = argparse.ArgumentParser(description="Migration des données JSON vers PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="Simulation sans écriture")
    parser.add_argument("--rollback", action="store_true", help="Annuler la migration")
    args = parser.parse_args()

    print("=" * 60)
    print("  MIGRATION JSON → POSTGRESQL — SuperAgent Morph")
    print("=" * 60)

    if args.rollback:
        session = get_session()
        try:
            rollback(session)
        finally:
            session.close()
        return

    if args.dry_run:
        print("  🔷 MODE DRY-RUN : aucune donnée ne sera écrite\n")
    else:
        print("  ⚠️  Mode réel : les données seront écrites dans PostgreSQL\n")

    session = get_session()
    try:
        # 1. Organisation par défaut
        print("\n📋 Étape 1/3 : Organisation et utilisateur")
        org = get_or_create_default_org(session, dry_run=args.dry_run)
        user = get_or_create_admin_user(session, org.org_id, dry_run=args.dry_run)

        # 2. Skills
        print("\n📋 Étape 2/3 : Migration des skills")
        skills_result = migrate_skills(session, org.org_id, user.user_id, dry_run=args.dry_run)
        print(f"  → {skills_result}")

        # 3. Checkpoints
        print("\n📋 Étape 3/3 : Migration des checkpoints")
        checkpoints_result = migrate_checkpoints(session, org.org_id, dry_run=args.dry_run)
        print(f"  → {checkpoints_result}")

        if not args.dry_run:
            session.commit()
            print("\n✅ Migration terminée avec succès !")
        else:
            session.rollback()
            print("\n🔷 DRY-RUN terminé. Aucune donnée écrite.")

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERREUR lors de la migration : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
