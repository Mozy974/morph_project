"""
Repository Pattern — Couche d'abstraction entre les modèles SQLAlchemy et la logique métier.

Chaque repository :
  - Encapsule les requêtes SQL pour une table
  - Injecte automatiquement org_id pour le multi-tenancy
  - Lève des exceptions métier (pas de SQL brutes dans le code applicatif)
"""
import uuid
from typing import Dict, List, Optional, Any, TypeVar, Generic
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from orchestrator.models import (
    Organization, User, Project, Job, Skill, Checkpoint, AuditLog, HumanValidation, ApiKey
)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Repository de base avec CRUD générique."""

    def __init__(self, db: Session, model_class: type, pk_field: str = None):
        self.db = db
        self.model = model_class
        # Inférer le nom de la PK depuis le modèle SQLAlchemy
        if pk_field is None:
            for col in model_class.__table__.primary_key.columns:
                pk_field = col.name
                break
        self.pk_field = pk_field

    def get_by_id(self, id_value: uuid.UUID) -> Optional[T]:
        pk_col = getattr(self.model, self.pk_field)
        return self.db.query(self.model).filter(pk_col == id_value).first()

    def list_all(self, org_id: uuid.UUID, limit: int = 100, offset: int = 0) -> List[T]:
        return (
            self.db.query(self.model)
            .filter(self.model.org_id == org_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count(self, org_id: uuid.UUID) -> int:
        pk_col = getattr(self.model, self.pk_field)
        return (
            self.db.query(func.count(pk_col))
            .filter(self.model.org_id == org_id)
            .scalar()
        )

    def delete(self, instance: T) -> None:
        self.db.delete(instance)
        self.db.flush()


# =============================================================================
# ORGANIZATION REPOSITORY
# =============================================================================

class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db: Session):
        super().__init__(db, Organization)

    def get_by_slug(self, slug: str) -> Optional[Organization]:
        return self.db.query(Organization).filter(Organization.slug == slug).first()

    def get_by_api_key_hash(self, key_hash: str) -> Optional[Organization]:
        return (
            self.db.query(Organization)
            .filter(Organization.api_key_hash == key_hash, Organization.is_active == True)
            .first()
        )

    def create(self, name: str, slug: str, api_key_hash: str) -> Organization:
        org = Organization(name=name, slug=slug, api_key_hash=api_key_hash)
        self.db.add(org)
        self.db.flush()
        return org


# =============================================================================
# USER REPOSITORY
# =============================================================================

class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, org_id: uuid.UUID, email: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.org_id == org_id, User.email == email)
            .first()
        )

    def create(self, org_id: uuid.UUID, email: str, display_name: str,
               role: str = "member") -> User:
        user = User(org_id=org_id, email=email, display_name=display_name, role=role)
        self.db.add(user)
        self.db.flush()
        return user


# =============================================================================
# SKILL REPOSITORY
# =============================================================================

class SkillRepository(BaseRepository[Skill]):
    def __init__(self, db: Session):
        super().__init__(db, Skill)

    def get_pending(self, org_id: uuid.UUID) -> List[Skill]:
        return (
            self.db.query(Skill)
            .filter(Skill.org_id == org_id, Skill.status == "PENDING_APPROVAL")
            .order_by(Skill.created_at.desc())
            .all()
        )

    def get_approved(self, org_id: uuid.UUID) -> List[Skill]:
        return (
            self.db.query(Skill)
            .filter(Skill.org_id == org_id, Skill.status == "APPROVED")
            .order_by(Skill.created_at.desc())
            .all()
        )

    def search_by_keywords(self, org_id: uuid.UUID, query: str) -> List[Skill]:
        """
        Recherche plein texte sur subject_key et keywords_json.
        Utilise l'index GIN PostgreSQL pour la performance.
        """
        return (
            self.db.query(Skill)
            .filter(
                Skill.org_id == org_id,
                Skill.status == "APPROVED",
                func.to_tsvector('french', Skill.subject_key).op('@@')(
                    func.plainto_tsquery('french', query)
                )
            )
            .order_by(Skill.created_at.desc())
            .limit(20)
            .all()
        )

    def create_pending(self, org_id: uuid.UUID, subject_key: str, directive_text: str,
                       error_context: str = "", keywords: List[str] = None,
                       source_job_id: Optional[uuid.UUID] = None) -> Skill:
        skill = Skill(
            org_id=org_id,
            status="PENDING_APPROVAL",
            subject_key=subject_key,
            directive_text=directive_text,
            error_context=error_context,
            keywords_json=keywords or [],
            source_job_id=source_job_id,
        )
        self.db.add(skill)
        self.db.flush()
        return skill

    def approve(self, skill_id: uuid.UUID, approved_by: uuid.UUID) -> Optional[Skill]:
        skill = self.get_by_id(skill_id)
        if skill and skill.status == "PENDING_APPROVAL":
            skill.status = "APPROVED"
            skill.approved_by = approved_by
            skill.approved_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.db.flush()
        return skill

    def reject(self, skill_id: uuid.UUID, rejected_by: uuid.UUID,
               reason: str = "") -> Optional[Skill]:
        skill = self.get_by_id(skill_id)
        if skill and skill.status == "PENDING_APPROVAL":
            skill.status = "REJECTED"
            skill.rejected_by = rejected_by
            skill.rejected_at = datetime.now(timezone.utc).replace(tzinfo=None)
            skill.rejection_reason = reason
            self.db.flush()
        return skill


# =============================================================================
# JOB REPOSITORY
# =============================================================================

class JobRepository(BaseRepository[Job]):
    def __init__(self, db: Session):
        super().__init__(db, Job)

    def create(self, org_id: uuid.UUID, task_text: str,
               project_id: Optional[uuid.UUID] = None,
               user_id: Optional[uuid.UUID] = None,
               max_retries: int = 2) -> Job:
        job = Job(
            org_id=org_id,
            project_id=project_id,
            user_id=user_id,
            task_text=task_text,
            status="PENDING",
            max_retries=max_retries,
        )
        self.db.add(job)
        self.db.flush()
        return job

    def update_status(self, job_id: uuid.UUID, status: str,
                      last_node: Optional[str] = None,
                      error_message: Optional[str] = None) -> Optional[Job]:
        job = self.get_by_id(job_id)
        if not job:
            return None

        job.status = status
        if last_node:
            job.last_node = last_node
        if error_message:
            job.error_message = error_message

        if status == "IN_PROGRESS" and not job.started_at:
            job.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        elif status in ("SUCCESS", "FAILED", "CANCELLED"):
            job.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        self.db.flush()
        return job

    def increment_retry(self, job_id: uuid.UUID) -> Optional[Job]:
        job = self.get_by_id(job_id)
        if job:
            job.retry_count += 1
            self.db.flush()
        return job

    def get_active_jobs(self, org_id: uuid.UUID) -> List[Job]:
        return (
            self.db.query(Job)
            .filter(
                Job.org_id == org_id,
                Job.status.in_(["PENDING", "IN_PROGRESS"])
            )
            .order_by(Job.created_at.desc())
            .all()
        )


# =============================================================================
# CHECKPOINT REPOSITORY
# =============================================================================

class CheckpointRepository(BaseRepository[Checkpoint]):
    def __init__(self, db: Session):
        super().__init__(db, Checkpoint)

    def save(self, job_id: uuid.UUID, org_id: uuid.UUID, state_blob: dict,
             last_node: str, retry_count: int = 0) -> Checkpoint:
        """Upsert : crée ou met à jour le checkpoint pour ce job."""
        existing = self.db.query(Checkpoint).filter(Checkpoint.job_id == job_id).first()
        if existing:
            existing.state_blob = state_blob
            existing.last_node = last_node
            existing.retry_count = retry_count
            existing.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + 7 * 86400
            self.db.flush()
            return existing

        cp = Checkpoint(
            job_id=job_id,
            org_id=org_id,
            state_blob=state_blob,
            last_node=last_node,
            retry_count=retry_count,
        )
        self.db.add(cp)
        self.db.flush()
        return cp

    def get_by_job_id(self, job_id: uuid.UUID) -> Optional[Checkpoint]:
        return self.db.query(Checkpoint).filter(Checkpoint.job_id == job_id).first()

    def has_checkpoint(self, job_id: uuid.UUID) -> bool:
        return self.db.query(Checkpoint).filter(Checkpoint.job_id == job_id).count() > 0

    def cleanup_expired(self) -> int:
        """Supprime les checkpoints expirés. Retourne le nombre supprimé."""
        result = self.db.query(Checkpoint).filter(
            Checkpoint.expires_at < datetime.now(timezone.utc).replace(tzinfo=None)
        ).delete()
        self.db.flush()
        return result


# =============================================================================
# AUDIT REPOSITORY
# =============================================================================

class AuditRepository:
    """Repository spécialisé pour l'audit trail (append-only)."""

    def __init__(self, db: Session):
        self.db = db

    def log(self, org_id: uuid.UUID, agent_name: str, action_type: str, status: str,
            job_id: Optional[uuid.UUID] = None,
            user_id: Optional[uuid.UUID] = None,
            duration_ms: Optional[int] = None,
            payload: Optional[dict] = None,
            error_message: Optional[str] = None) -> AuditLog:
        """Enregistre un événement d'audit (append-only)."""
        entry = AuditLog(
            org_id=org_id,
            job_id=job_id,
            user_id=user_id,
            agent_name=agent_name,
            action_type=action_type,
            status=status,
            duration_ms=duration_ms,
            payload_json=payload,
            error_message=error_message,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def get_by_job(self, job_id: uuid.UUID, limit: int = 100) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.job_id == job_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_agent(self, org_id: uuid.UUID, agent_name: str,
                     limit: int = 50) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.org_id == org_id, AuditLog.agent_name == agent_name)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_recent(self, org_id: uuid.UUID, limit: int = 50) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.org_id == org_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )


# =============================================================================
# API KEY REPOSITORY
# =============================================================================

class ApiKeyRepository(BaseRepository[ApiKey]):
    def __init__(self, db: Session):
        super().__init__(db, ApiKey)

    def get_active_by_provider(self, org_id: uuid.UUID, provider: str) -> Optional[ApiKey]:
        return (
            self.db.query(ApiKey)
            .filter(
                ApiKey.org_id == org_id,
                ApiKey.provider == provider,
                ApiKey.is_active == True,
                (ApiKey.expires_at.is_(None) | (ApiKey.expires_at > func.now()))
            )
            .order_by(ApiKey.usage_count.asc())
            .first()
        )

    def increment_usage(self, api_key_id: uuid.UUID) -> None:
        self.db.query(ApiKey).filter(ApiKey.api_key_id == api_key_id).update(
            {
                ApiKey.usage_count: ApiKey.usage_count + 1,
                ApiKey.last_used_at: datetime.now(timezone.utc).replace(tzinfo=None),
            }
        )
        self.db.flush()
