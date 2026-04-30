"""create governance and release gate tables

Revision ID: 0001
Revises:
Create Date: 2026-04-30 09:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_rule_approval_requests",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("rule_id", sa.Integer(), nullable=False, index=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "governance_brain_decisions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "approval_request_id",
            sa.Integer(),
            sa.ForeignKey("notification_rule_approval_requests.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("evaluated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("governance_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reasons_json", sa.Text(), nullable=True),
        sa.Column("signals_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "release_gate_decisions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "approval_request_id",
            sa.Integer(),
            sa.ForeignKey("notification_rule_approval_requests.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("gate_name", sa.String(), nullable=False),
        sa.Column("passed", sa.Integer(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("evaluated_by_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("release_gate_decisions")
    op.drop_table("governance_brain_decisions")
    op.drop_table("notification_rule_approval_requests")
