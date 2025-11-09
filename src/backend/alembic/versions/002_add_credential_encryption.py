"""Add credential encryption support to users table

Revision ID: 002_add_credential_encryption
Revises: 001_initial_schema
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_credential_encryption'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add credential encryption fields to users table"""
    
    # Add encryption_key column (base64-encoded Fernet key)
    op.add_column(
        'users',
        sa.Column('encryption_key', sa.String(255), nullable=True)
    )
    
    # Convert plaid_access_token from String to LargeBinary
    # This requires dropping and recreating the column
    with op.batch_alter_table('users') as batch_op:
        # Create new LargeBinary columns
        batch_op.add_column(
            sa.Column('plaid_access_token_encrypted', sa.LargeBinary(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('alpaca_api_key_encrypted', sa.LargeBinary(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('alpaca_secret_key_encrypted', sa.LargeBinary(), nullable=True)
        )


def downgrade() -> None:
    """Remove credential encryption fields from users table"""
    
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('plaid_access_token_encrypted')
        batch_op.drop_column('alpaca_api_key_encrypted')
        batch_op.drop_column('alpaca_secret_key_encrypted')
        batch_op.drop_column('encryption_key')
