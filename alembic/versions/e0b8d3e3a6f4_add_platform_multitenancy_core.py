"""add_platform_multitenancy_core

Revision ID: e0b8d3e3a6f4
Revises: d5d2333fb753
Create Date: 2026-03-12 10:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e0b8d3e3a6f4"
down_revision: Union[str, None] = "d5d2333fb753"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'PLATFORM_OWNER'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'TENANT_ADMIN'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'TENANT_STAFF'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'TENANT_EMPLOYEE'")

    op.add_column("organisations", sa.Column("slug", sa.String(length=120), nullable=True))
    op.add_column("organisations", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("organisations", sa.Column("portal_plan", sa.String(length=50), nullable=False, server_default="free"))
    op.add_column("organisations", sa.Column("portal_expires_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_organisations_slug"), "organisations", ["slug"], unique=True)

    op.add_column("users", sa.Column("must_reset_password", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("plan_code", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("billing_interval", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("current_period_start", sa.DateTime(), nullable=True),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subscriptions_organisation_id"), "subscriptions", ["organisation_id"], unique=False)

    op.create_table(
        "subscription_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("subscription_id", sa.String(length=36), nullable=True),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_subscription_events_provider_event_id"),
        "subscription_events",
        ["provider_event_id"],
        unique=True,
    )

    op.create_table(
        "tenant_invitations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tenant_invitations_email"), "tenant_invitations", ["email"], unique=False)
    op.create_index(
        op.f("ix_tenant_invitations_organisation_id"),
        "tenant_invitations",
        ["organisation_id"],
        unique=False,
    )

    op.alter_column("organisations", "is_active", server_default=None)
    op.alter_column("organisations", "portal_plan", server_default=None)
    op.alter_column("users", "must_reset_password", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_tenant_invitations_organisation_id"), table_name="tenant_invitations")
    op.drop_index(op.f("ix_tenant_invitations_email"), table_name="tenant_invitations")
    op.drop_table("tenant_invitations")

    op.drop_index(op.f("ix_subscription_events_provider_event_id"), table_name="subscription_events")
    op.drop_table("subscription_events")

    op.drop_index(op.f("ix_subscriptions_organisation_id"), table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_column("users", "must_reset_password")

    op.drop_index(op.f("ix_organisations_slug"), table_name="organisations")
    op.drop_column("organisations", "portal_expires_at")
    op.drop_column("organisations", "portal_plan")
    op.drop_column("organisations", "is_active")
    op.drop_column("organisations", "slug")
