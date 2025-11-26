"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create providers table
    op.create_table(
        'providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('base_api_url', sa.Text, nullable=True),
        sa.Column('schema_version', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text, nullable=True)
    )

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id'), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('key_encrypted', sa.Text, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(200), unique=True, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # Create import_jobs table
    op.create_table(
        'import_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id'), nullable=False),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('api_keys.id'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), default='running'),
        sa.Column('requested_range', postgresql.JSONB, nullable=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('error_details', sa.Text, nullable=True),
        sa.Column('conversations_imported', sa.Integer, default=0),
        sa.Column('messages_imported', sa.Integer, default=0),
        sa.Column('artifacts_imported', sa.Integer, default=0)
    )
    op.create_index('idx_import_job_status', 'import_jobs', ['status'])

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id'), nullable=False),
        sa.Column('provider_conversation_id', sa.Text, nullable=True),
        sa.Column('title', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('origin', sa.String(50), default='api'),
        sa.Column('import_job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('import_jobs.id'), nullable=True),
        sa.Column('import_notes', sa.Text, nullable=True),
        sa.Column('archived', sa.Boolean, default=False, nullable=False),
        sa.Column('raw_metadata', postgresql.JSONB, nullable=True)
    )
    op.create_index('idx_conversation_started_at', 'conversations', ['started_at'])
    op.create_index('idx_conversation_provider', 'conversations', ['provider_id'])
    op.create_unique_constraint('uq_provider_conversation', 'conversations', ['provider_id', 'provider_conversation_id'])

    # Create conversation_projects join table
    op.create_table(
        'conversation_projects',
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id'), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), primary_key=True)
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('provider_message_id', sa.Text, nullable=True),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sequence_index', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('raw_metadata', postgresql.JSONB, nullable=True)
    )
    op.create_index('idx_message_conversation', 'messages', ['conversation_id'])
    op.create_index('idx_message_sequence', 'messages', ['conversation_id', 'sequence_index'])

    # Create artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('messages.id'), nullable=True),
        sa.Column('artifact_type', sa.String(50), nullable=False),
        sa.Column('provider_artifact_id', sa.Text, nullable=True),
        sa.Column('filename', sa.Text, nullable=True),
        sa.Column('mime_type', sa.String(200), nullable=True),
        sa.Column('storage_path', sa.Text, nullable=True),
        sa.Column('download_status', sa.String(50), default='pending'),
        sa.Column('download_error', sa.Text, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('raw_metadata', postgresql.JSONB, nullable=True)
    )
    op.create_index('idx_artifact_conversation', 'artifacts', ['conversation_id'])

    # Create conversation_edits table (for v1.1+)
    op.create_table(
        'conversation_edits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('edited_markdown', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_modified_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('base_conversation_hash', sa.String(64), nullable=True)
    )

    # Seed initial providers
    providers_table = sa.table(
        'providers',
        sa.column('id', postgresql.UUID),
        sa.column('name', sa.String),
        sa.column('display_name', sa.String),
        sa.column('base_api_url', sa.Text),
        sa.column('schema_version', sa.String),
        sa.column('notes', sa.Text)
    )

    op.bulk_insert(
        providers_table,
        [
            {
                'id': uuid.uuid4(),
                'name': 'openai',
                'display_name': 'OpenAI / ChatGPT',
                'base_api_url': 'https://api.openai.com/v1',
                'schema_version': '1.0',
                'notes': 'OpenAI ChatGPT provider'
            },
            {
                'id': uuid.uuid4(),
                'name': 'anthropic',
                'display_name': 'Anthropic / Claude',
                'base_api_url': 'https://api.anthropic.com/v1',
                'schema_version': '1.0',
                'notes': 'Anthropic Claude provider'
            }
        ]
    )


def downgrade() -> None:
    op.drop_table('conversation_edits')
    op.drop_table('artifacts')
    op.drop_table('messages')
    op.drop_table('conversation_projects')
    op.drop_table('conversations')
    op.drop_table('import_jobs')
    op.drop_table('projects')
    op.drop_table('api_keys')
    op.drop_table('providers')
