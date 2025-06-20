"""Create conversation and message tables

Revision ID: 08d71511ecdf
Revises:
Create Date: 2025-06-09 20:13:52.480773

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "08d71511ecdf"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("total_messages", sa.Integer(), nullable=True),
        sa.Column(
            "last_activity",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("conversations_pkey")),
    )
    op.create_index(
        op.f("conversations_session_id_idx"),
        "conversations",
        ["session_id"],
        unique=True,
    )
    op.create_index(
        op.f("conversations_user_id_idx"), "conversations", ["user_id"], unique=False
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("conversation_id", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("agent_name", sa.String(length=100), nullable=True),
        sa.Column("agent_used", sa.String(length=100), nullable=True),
        sa.Column("intent", sa.String(length=100), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("usage_data", sa.JSON(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("messages_conversation_id_conversations_fkey"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("messages_pkey")),
    )
    op.create_index(
        op.f("messages_conversation_id_idx"),
        "messages",
        ["conversation_id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("messages_conversation_id_idx"), table_name="messages")
    op.drop_table("messages")
    op.drop_index(op.f("conversations_user_id_idx"), table_name="conversations")
    op.drop_index(op.f("conversations_session_id_idx"), table_name="conversations")
    op.drop_table("conversations")
    # ### end Alembic commands ###
