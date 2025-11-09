"""Initial schema migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all APEX database tables"""
    
    # Create pgvector extension
    op.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('profile_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'])
    op.create_index(op.f('ix_users_email'), 'users', ['email'])
    
    # Create portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('account_number', sa.String(50), nullable=True),
        sa.Column('total_value', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('cash_balance', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('buying_power', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('broker_id', sa.String(50), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portfolios_user_id'), 'portfolios', ['user_id'])
    
    # Create positions table
    op.create_table(
        'positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('average_cost', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('market_value', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('unrealized_gain_loss', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('unrealized_gain_loss_pct', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_positions_portfolio_id'), 'positions', ['portfolio_id'])
    op.create_index(op.f('ix_positions_symbol'), 'positions', ['symbol'])
    
    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('trade_type', sa.String(10), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_value', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('commission', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('execution_timestamp', sa.DateTime(), nullable=True),
        sa.Column('voice_command', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('command_text', sa.String(500), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('recommendation', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trades_user_id'), 'trades', ['user_id'])
    op.create_index(op.f('ix_trades_portfolio_id'), 'trades', ['portfolio_id'])
    op.create_index(op.f('ix_trades_symbol'), 'trades', ['symbol'])
    op.create_index(op.f('ix_trades_status'), 'trades', ['status'])
    
    # Create goals table
    op.create_table(
        'goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('current_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('compound_interest_data', sa.JSON(), nullable=True),
        sa.Column('risk_assessment', sa.JSON(), nullable=True),
        sa.Column('strategy_recommendation', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goals_user_id'), 'goals', ['user_id'])
    op.create_index(op.f('ix_goals_status'), 'goals', ['status'])
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('billing_cycle', sa.String(20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('waste_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('usage_pattern', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'])
    op.create_index(op.f('ix_subscriptions_is_active'), 'subscriptions', ['is_active'])
    
    # Create performance_records table
    op.create_table(
        'performance_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('record_date', sa.Date(), nullable=False),
        sa.Column('total_return_pct', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('max_drawdown_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('win_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('trades_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_performance_records_portfolio_id'), 'performance_records', ['portfolio_id'])
    op.create_index(op.f('ix_performance_records_record_date'), 'performance_records', ['record_date'])
    
    # Create agent_decision_logs table
    op.create_table(
        'agent_decision_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('decision_type', sa.String(50), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('output_recommendation', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('execution_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default='now()'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_decision_logs_user_id'), 'agent_decision_logs', ['user_id'])
    op.create_index(op.f('ix_agent_decision_logs_agent_type'), 'agent_decision_logs', ['agent_type'])
    op.create_index(op.f('ix_agent_decision_logs_created_at'), 'agent_decision_logs', ['created_at'])


def downgrade() -> None:
    """Drop all APEX tables"""
    op.drop_index(op.f('ix_agent_decision_logs_created_at'), table_name='agent_decision_logs')
    op.drop_index(op.f('ix_agent_decision_logs_agent_type'), table_name='agent_decision_logs')
    op.drop_index(op.f('ix_agent_decision_logs_user_id'), table_name='agent_decision_logs')
    op.drop_table('agent_decision_logs')
    
    op.drop_index(op.f('ix_performance_records_record_date'), table_name='performance_records')
    op.drop_index(op.f('ix_performance_records_portfolio_id'), table_name='performance_records')
    op.drop_table('performance_records')
    
    op.drop_index(op.f('ix_subscriptions_is_active'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    
    op.drop_index(op.f('ix_goals_status'), table_name='goals')
    op.drop_index(op.f('ix_goals_user_id'), table_name='goals')
    op.drop_table('goals')
    
    op.drop_index(op.f('ix_trades_status'), table_name='trades')
    op.drop_index(op.f('ix_trades_symbol'), table_name='trades')
    op.drop_index(op.f('ix_trades_portfolio_id'), table_name='trades')
    op.drop_index(op.f('ix_trades_user_id'), table_name='trades')
    op.drop_table('trades')
    
    op.drop_index(op.f('ix_positions_symbol'), table_name='positions')
    op.drop_index(op.f('ix_positions_portfolio_id'), table_name='positions')
    op.drop_table('positions')
    
    op.drop_index(op.f('ix_portfolios_user_id'), table_name='portfolios')
    op.drop_table('portfolios')
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
    
    op.execute(text('DROP EXTENSION IF EXISTS vector'))
