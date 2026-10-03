from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('leads',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('contact', sa.String(length=255), nullable=True),
    sa.Column('request', sa.Text(), nullable=True),
    sa.Column('source', sa.Enum('telegram_bot', 'telegram_account', 'manual', name='leadsource', native_enum=False, length=32), nullable=False),
    sa.Column('status', sa.Enum('new', 'in_progress', 'won', 'lost', name='leadstatus', native_enum=False, length=32), server_default='new', nullable=False),
    sa.Column('telegram_chat_id', sa.BigInteger(), nullable=True),
    sa.Column('telegram_username', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_leads'))
    )
    op.create_index(op.f('ix_leads_source'), 'leads', ['source'], unique=False)
    op.create_index(op.f('ix_leads_status'), 'leads', ['status'], unique=False)
    op.create_index(op.f('ix_leads_telegram_chat_id'), 'leads', ['telegram_chat_id'], unique=False)
    op.create_table('tags',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('color', sa.String(length=7), server_default='#6366f1', nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tags')),
    sa.UniqueConstraint('name', name=op.f('uq_tags_name'))
    )
    op.create_table('lead_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name=op.f('fk_lead_messages_lead_id_leads'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lead_messages'))
    )
    op.create_index(op.f('ix_lead_messages_lead_id'), 'lead_messages', ['lead_id'], unique=False)
    op.create_table('lead_tags',
    sa.Column('lead_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name=op.f('fk_lead_tags_lead_id_leads'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name=op.f('fk_lead_tags_tag_id_tags'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('lead_id', 'tag_id', name=op.f('pk_lead_tags'))
    )
    op.create_index(op.f('ix_lead_tags_tag_id'), 'lead_tags', ['tag_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_lead_tags_tag_id'), table_name='lead_tags')
    op.drop_table('lead_tags')
    op.drop_index(op.f('ix_lead_messages_lead_id'), table_name='lead_messages')
    op.drop_table('lead_messages')
    op.drop_table('tags')
    op.drop_index(op.f('ix_leads_telegram_chat_id'), table_name='leads')
    op.drop_index(op.f('ix_leads_status'), table_name='leads')
    op.drop_index(op.f('ix_leads_source'), table_name='leads')
    op.drop_table('leads')
