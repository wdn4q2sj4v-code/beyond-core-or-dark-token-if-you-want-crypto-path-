"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-30

Creates the three core tables:
  - notification_rule_approval_requests
  - governance_brain_decisions
  - release_gate_decisions
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
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_notification_rule_approval_requests_id"),
        "notification_rule_approval_requests",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_rule_approval_requests_rule_id"),
        "notification_rule_approval_requests",
        ["rule_id"],
        unique=False,
    )

    op.create_table(
        "governance_brain_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("approval_request_id", sa.Integer(), nullable=False),
        sa.Column("evaluated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("governance_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reasons_json", sa.Text(), nullable=True),
        sa.Column("signals_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["approval_request_id"],
            ["notification_rule_approval_requests.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_governance_brain_decisions_id"),
        "governance_brain_decisions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_governance_brain_decisions_approval_request_id"),
        "governance_brain_decisions",
        ["approval_request_id"],
        unique=False,
    )

    op.create_table(
        "release_gate_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("approval_request_id", sa.Integer(), nullable=False),
        sa.Column("gate_name", sa.String(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("evaluated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["approval_request_id"],
            ["notification_rule_approval_requests.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_release_gate_decisions_id"),
        "release_gate_decisions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_release_gate_decisions_approval_request_id"),
        "release_gate_decisions",
        ["approval_request_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_release_gate_decisions_approval_request_id"),
        table_name="release_gate_decisions",
    )
    op.drop_index(
        op.f("ix_release_gate_decisions_id"),
        table_name="release_gate_decisions",
    )
    op.drop_table("release_gate_decisions")

    op.drop_index(
        op.f("ix_governance_brain_decisions_approval_request_id"),
        table_name="governance_brain_decisions",
    )
    op.drop_index(
        op.f("ix_governance_brain_decisions_id"),
        table_name="governance_brain_decisions",
    )
    op.drop_table("governance_brain_decisions")

    op.drop_index(
        op.f("ix_notification_rule_approval_requests_rule_id"),
        table_name="notification_rule_approval_requests",
    )
    op.drop_index(
        op.f("ix_notification_rule_approval_requests_id"),
        table_name="notification_rule_approval_requests",
    )
    op.drop_table("notification_rule_approval_requests")
