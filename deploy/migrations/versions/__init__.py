"""Alembic script template for autogenerate."""
# type: ignore
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Placeholder for future migrations."""
    pass


def downgrade() -> None:
    """Placeholder for future migrations."""
    pass
