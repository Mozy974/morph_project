"""Alembic migration script template."""
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Migration initiale : création de toutes les tables.
    Exécuter d'abord deploy/schema.sql pour les triggers, RLS et partitions,
    ou laisser Alembic créer les tables via les modèles SQLAlchemy.
    """
    # Les tables sont créées automatiquement par --autogenerate
    # Les triggers, RLS et partitions sont dans deploy/schema.sql
    pass


def downgrade() -> None:
    """
    Annulation : suppression de toutes les tables.
    """
    pass
