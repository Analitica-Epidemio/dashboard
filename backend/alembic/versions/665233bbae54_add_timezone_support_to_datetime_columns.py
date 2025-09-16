"""add timezone support to datetime columns

Revision ID: 665233bbae54
Revises: 818cbbda06dd
Create Date: 2025-09-16 03:36:44.420829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # Always import sqlmodel for SQLModel types


# revision identifiers, used by Alembic.
revision: str = '665233bbae54'
down_revision: Union[str, Sequence[str], None] = '818cbbda06dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Convert datetime columns to TIMESTAMP WITH TIME ZONE for proper timezone support

    # Users table
    op.execute("ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN last_login TYPE TIMESTAMP WITH TIME ZONE USING last_login AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN locked_until TYPE TIMESTAMP WITH TIME ZONE USING locked_until AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN password_reset_expires TYPE TIMESTAMP WITH TIME ZONE USING password_reset_expires AT TIME ZONE 'UTC'")

    # User sessions table
    op.execute("ALTER TABLE user_sessions ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE user_sessions ALTER COLUMN expires_at TYPE TIMESTAMP WITH TIME ZONE USING expires_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE user_sessions ALTER COLUMN last_activity TYPE TIMESTAMP WITH TIME ZONE USING last_activity AT TIME ZONE 'UTC'")

    # User logins table
    op.execute("ALTER TABLE user_logins ALTER COLUMN attempted_at TYPE TIMESTAMP WITH TIME ZONE USING attempted_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    """Downgrade schema."""
    # Convert back to TIMESTAMP WITHOUT TIME ZONE

    # Users table
    op.execute("ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE USING updated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN last_login TYPE TIMESTAMP WITHOUT TIME ZONE USING last_login AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN locked_until TYPE TIMESTAMP WITHOUT TIME ZONE USING locked_until AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN password_reset_expires TYPE TIMESTAMP WITHOUT TIME ZONE USING password_reset_expires AT TIME ZONE 'UTC'")

    # User sessions table
    op.execute("ALTER TABLE user_sessions ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE user_sessions ALTER COLUMN expires_at TYPE TIMESTAMP WITHOUT TIME ZONE USING expires_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE user_sessions ALTER COLUMN last_activity TYPE TIMESTAMP WITHOUT TIME ZONE USING last_activity AT TIME ZONE 'UTC'")

    # User logins table
    op.execute("ALTER TABLE user_logins ALTER COLUMN attempted_at TYPE TIMESTAMP WITHOUT TIME ZONE USING attempted_at AT TIME ZONE 'UTC'")
