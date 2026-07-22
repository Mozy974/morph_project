"""
Modèles SQLAlchemy pour le SuperAgent Morph — Multi-Tenant, Audit Trail, HITL.
Correspond au schéma PostgreSQL défini dans deploy/schema.sql.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy import (
    Column, String, Integer, Boolean, BigInteger, Float, Text, UUID, ForeignKey,
    UniqueConstraint, CheckConstraint, Index, JSON, TIMESTAMP, func, event
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID


class Base(DeclarativeBase):
    pass


# =============================================================================
# MIXIN : Timestamps automatiques
# =============================================================================

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )


# =============================================================================
# ORGANIZATIONS
# =============================================================================

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Relations
    users: Mapped[List["User"]] = relationship(back_populates="organization", lazy="selectin")
    projects: Mapped[List["Project"]] = relationship(back_populates="organization", lazy="selectin")
    jobs: Mapped[List["Job"]] = relationship(back_populates="organization", lazy="dynamic")
    skills: Mapped[List["Skill"]] = relationship(back_populates="organization", lazy="dynamic")
    api_keys: Mapped[List["ApiKey"]] = relationship(back_populates="organization", lazy="selectin")


# =============================================================================
# USERS
# =============================================================================

class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("org_id", "email", name="uq_users_org_email"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), default="member", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    # Relations
    organization: Mapped["Organization"] = relationship(back_populates="users")
    jobs: Mapped[List["Job"]] = relationship(back_populates="user", lazy="dynamic")
    approved_skills: Mapped[List["Skill"]] = relationship(
        back_populates="approver", foreign_keys="Skill.approved_by", lazy="dynamic"
    )
    validations: Mapped[List["HumanValidation"]] = relationship(back_populates="user", lazy="dynamic")


# =============================================================================
# PROJECTS
# =============================================================================

class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    repo_url: Mapped[Optional[str]] = mapped_column(String(500))
    settings_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Relations
    organization: Mapped["Organization"] = relationship(back_populates="projects")
    jobs: Mapped[List["Job"]] = relationship(back_populates="project", lazy="dynamic")


# =============================================================================
# JOBS
# =============================================================================

class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID, ForeignKey("projects.project_id", ondelete="SET NULL")
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID, ForeignKey("users.user_id", ondelete="SET NULL")
    )
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING", nullable=False
    )
    last_node: Mapped[str] = mapped_column(String(50), default="START")
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    # Relations
    organization: Mapped["Organization"] = relationship(back_populates="jobs")
    project: Mapped[Optional["Project"]] = relationship(back_populates="jobs")
    user: Mapped[Optional["User"]] = relationship(back_populates="jobs")
    checkpoint: Mapped[Optional["Checkpoint"]] = relationship(back_populates="job", uselist=False)
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="job", lazy="dynamic")
    validations: Mapped[List["HumanValidation"]] = relationship(back_populates="job", lazy="dynamic")


# =============================================================================
# SKILLS
# =============================================================================

class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    skill_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING_APPROVAL", nullable=False
    )
    subject_key: Mapped[str] = mapped_column(String(255), nullable=False)
    directive_text: Mapped[str] = mapped_column(Text, nullable=False)
    error_context: Mapped[Optional[str]] = mapped_column(Text)
    keywords_json: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    sha256_hash: Mapped[Optional[str]] = mapped_column(String(64))
    source_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID, ForeignKey("jobs.job_id", ondelete="SET NULL")
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID, ForeignKey("users.user_id", ondelete="SET NULL")
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    rejected_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID, ForeignKey("users.user_id", ondelete="SET NULL")
    )
    rejected_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relations
    organization: Mapped["Organization"] = relationship(back_populates="skills")
    approver: Mapped[Optional["User"]] = relationship(
        back_populates="approved_skills", foreign_keys=[approved_by]
    )
    source_job: Mapped[Optional["Job"]] = relationship()
    validations: Mapped[List["HumanValidation"]] = relationship(back_populates="skill", lazy="dynamic")


# =============================================================================
# CHECKPOINTS
# =============================================================================

class Checkpoint(Base, TimestampMixin):
    __tablename__ = "checkpoints"

    job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, ForeignKey("jobs.job_id", ondelete="CASCADE"), primary_key=True
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False
    )
    state_blob: Mapped[dict] = mapped_column(JSONB, nullable=False)
    last_node: Mapped[str] = mapped_column(String(50), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7),
        nullable=False
    )

    # Relations
    job: Mapped["Job"] = relationship(back_populates="checkpoint")
    organization: Mapped["Organization"] = relationship()


# =============================================================================
# AUDIT LOGS
# =============================================================================

class AuditLog(Base):
    """Append-only : pas de updated_at, pas d'UPDATE possible."""
    __tablename__ = "audit_logs"

    log_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID, ForeignKey("jobs.job_id", ondelete="SET NULL")
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID, ForeignKey("users.user_id", ondelete="SET NULL")
    )
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relations
    organization: Mapped["Organization"] = relationship()
    job: Mapped[Optional["Job"]] = relationship(back_populates="audit_logs")


# =============================================================================
# HUMAN VALIDATIONS
# =============================================================================

class HumanValidation(Base):
    __tablename__ = "human_validations"

    validation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID, ForeignKey("jobs.job_id", ondelete="SET NULL")
    )
    skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID, ForeignKey("skills.skill_id", ondelete="SET NULL")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    context_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relations
    organization: Mapped["Organization"] = relationship()
    job: Mapped[Optional["Job"]] = relationship(back_populates="validations")
    skill: Mapped[Optional["Skill"]] = relationship(back_populates="validations")
    user: Mapped["User"] = relationship(back_populates="validations")


# =============================================================================
# API KEYS (BYOK — Bring Your Own Key)
# =============================================================================

class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    api_key_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID, ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False
    )
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    usage_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    # Relations
    organization: Mapped["Organization"] = relationship(back_populates="api_keys")
