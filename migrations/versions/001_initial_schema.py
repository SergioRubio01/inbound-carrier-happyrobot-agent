"""Initial schema for HappyRobot FDE

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-08-15 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create carriers table
    op.create_table(
        "carriers",
        sa.Column("carrier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mc_number", sa.String(length=20), nullable=False),
        sa.Column("dot_number", sa.String(length=20), nullable=True),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("dba_name", sa.String(length=255), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("operating_status", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("insurance_on_file", sa.Boolean(), nullable=True),
        sa.Column("bipd_required", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("bipd_on_file", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("cargo_required", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("cargo_on_file", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("bond_required", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("bond_on_file", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("safety_rating", sa.String(length=20), nullable=True),
        sa.Column("safety_rating_date", sa.Date(), nullable=True),
        sa.Column(
            "safety_scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "primary_contact", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("address", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("eligibility_notes", sa.Text(), nullable=True),
        sa.Column("last_verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("verification_source", sa.String(length=50), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("carrier_id"),
    )
    op.create_index(
        op.f("ix_carriers_mc_number"), "carriers", ["mc_number"], unique=True
    )
    op.create_index(
        op.f("ix_carriers_dot_number"), "carriers", ["dot_number"], unique=False
    )

    # Create loads table
    op.create_table(
        "loads",
        sa.Column("load_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_number", sa.String(length=50), nullable=True),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column("origin_city", sa.String(length=100), nullable=False),
        sa.Column("origin_state", sa.String(length=2), nullable=False),
        sa.Column("origin_zip", sa.String(length=10), nullable=True),
        sa.Column(
            "origin_coordinates", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "origin_facility", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("destination_city", sa.String(length=100), nullable=False),
        sa.Column("destination_state", sa.String(length=2), nullable=False),
        sa.Column("destination_zip", sa.String(length=10), nullable=True),
        sa.Column(
            "destination_coordinates",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "destination_facility",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("pickup_date", sa.Date(), nullable=False),
        sa.Column("pickup_time_start", sa.Time(), nullable=True),
        sa.Column("pickup_time_end", sa.Time(), nullable=True),
        sa.Column("pickup_appointment_required", sa.Boolean(), nullable=True),
        sa.Column("delivery_date", sa.Date(), nullable=False),
        sa.Column("delivery_time_start", sa.Time(), nullable=True),
        sa.Column("delivery_time_end", sa.Time(), nullable=True),
        sa.Column("delivery_appointment_required", sa.Boolean(), nullable=True),
        sa.Column("equipment_type", sa.String(length=50), nullable=False),
        sa.Column(
            "equipment_requirements",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("pieces", sa.Integer(), nullable=True),
        sa.Column("commodity_type", sa.String(length=100), nullable=True),
        sa.Column("commodity_description", sa.Text(), nullable=True),
        sa.Column("dimensions", sa.String(length=100), nullable=True),
        sa.Column("hazmat", sa.Boolean(), nullable=True),
        sa.Column("hazmat_class", sa.String(length=20), nullable=True),
        sa.Column("miles", sa.Integer(), nullable=False),
        sa.Column("estimated_transit_hours", sa.Integer(), nullable=True),
        sa.Column("route_notes", sa.Text(), nullable=True),
        sa.Column("loadboard_rate", sa.NUMERIC(precision=10, scale=2), nullable=False),
        sa.Column("fuel_surcharge", sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column(
            "accessorials", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("minimum_rate", sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column("maximum_rate", sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column("target_rate", sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column(
            "auto_accept_threshold", sa.NUMERIC(precision=10, scale=2), nullable=True
        ),
        sa.Column("broker_company", sa.String(length=255), nullable=True),
        sa.Column(
            "broker_contact", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("status_changed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("booked_by_carrier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("booked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("special_requirements", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("urgency", sa.String(length=20), nullable=True),
        sa.Column("priority_score", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["booked_by_carrier_id"],
            ["carriers.carrier_id"],
        ),
        sa.PrimaryKeyConstraint("load_id"),
    )
    op.create_index(
        op.f("ix_loads_reference_number"), "loads", ["reference_number"], unique=True
    )
    op.create_index(
        op.f("ix_loads_origin_city"), "loads", ["origin_city"], unique=False
    )
    op.create_index(
        op.f("ix_loads_origin_state"), "loads", ["origin_state"], unique=False
    )
    op.create_index(
        op.f("ix_loads_destination_city"), "loads", ["destination_city"], unique=False
    )
    op.create_index(
        op.f("ix_loads_destination_state"), "loads", ["destination_state"], unique=False
    )
    op.create_index(
        op.f("ix_loads_pickup_date"), "loads", ["pickup_date"], unique=False
    )
    op.create_index(
        op.f("ix_loads_equipment_type"), "loads", ["equipment_type"], unique=False
    )
    op.create_index(op.f("ix_loads_miles"), "loads", ["miles"], unique=False)
    op.create_index(
        op.f("ix_loads_loadboard_rate"), "loads", ["loadboard_rate"], unique=False
    )
    op.create_index(op.f("ix_loads_status"), "loads", ["status"], unique=False)
    op.create_index(op.f("ix_loads_is_active"), "loads", ["is_active"], unique=False)

    # Create calls table
    op.create_table(
        "calls",
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_call_id", sa.String(length=100), nullable=True),
        sa.Column("session_id", sa.String(length=100), nullable=True),
        sa.Column("mc_number", sa.String(length=20), nullable=True),
        sa.Column("carrier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("caller_phone", sa.String(length=20), nullable=True),
        sa.Column("caller_name", sa.String(length=100), nullable=True),
        sa.Column("load_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "multiple_loads_discussed",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=True,
        ),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("call_type", sa.String(length=30), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=True),
        sa.Column("agent_type", sa.String(length=30), nullable=True),
        sa.Column("agent_id", sa.String(length=50), nullable=True),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column(
            "outcome_confidence", sa.NUMERIC(precision=3, scale=2), nullable=True
        ),
        sa.Column("sentiment", sa.String(length=20), nullable=True),
        sa.Column("sentiment_score", sa.NUMERIC(precision=3, scale=2), nullable=True),
        sa.Column(
            "sentiment_breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("initial_offer", sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column("final_rate", sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column("rate_accepted", sa.Boolean(), nullable=True),
        sa.Column(
            "extracted_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("transcript_summary", sa.Text(), nullable=True),
        sa.Column("key_points", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("transferred_to_human", sa.Boolean(), nullable=True),
        sa.Column("transfer_reason", sa.String(length=100), nullable=True),
        sa.Column("transferred_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("assigned_rep_id", sa.String(length=50), nullable=True),
        sa.Column("follow_up_required", sa.Boolean(), nullable=True),
        sa.Column("follow_up_reason", sa.Text(), nullable=True),
        sa.Column("follow_up_deadline", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("follow_up_completed", sa.Boolean(), nullable=True),
        sa.Column("recording_url", sa.Text(), nullable=True),
        sa.Column("recording_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("quality_issues", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["carrier_id"],
            ["carriers.carrier_id"],
        ),
        sa.ForeignKeyConstraint(
            ["load_id"],
            ["loads.load_id"],
        ),
        sa.PrimaryKeyConstraint("call_id"),
    )
    op.create_index(
        op.f("ix_calls_external_call_id"), "calls", ["external_call_id"], unique=False
    )
    op.create_index(op.f("ix_calls_mc_number"), "calls", ["mc_number"], unique=False)
    op.create_index(op.f("ix_calls_carrier_id"), "calls", ["carrier_id"], unique=False)
    op.create_index(
        op.f("ix_calls_caller_phone"), "calls", ["caller_phone"], unique=False
    )
    op.create_index(op.f("ix_calls_load_id"), "calls", ["load_id"], unique=False)
    op.create_index(op.f("ix_calls_start_time"), "calls", ["start_time"], unique=False)
    op.create_index(op.f("ix_calls_end_time"), "calls", ["end_time"], unique=False)
    op.create_index(op.f("ix_calls_outcome"), "calls", ["outcome"], unique=False)
    op.create_index(op.f("ix_calls_sentiment"), "calls", ["sentiment"], unique=False)
    op.create_index(
        op.f("ix_calls_transferred_to_human"),
        "calls",
        ["transferred_to_human"],
        unique=False,
    )
    op.create_index(
        op.f("ix_calls_follow_up_required"),
        "calls",
        ["follow_up_required"],
        unique=False,
    )

    # Create negotiations table
    op.create_table(
        "negotiations",
        sa.Column("negotiation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("load_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("carrier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("mc_number", sa.String(length=20), nullable=True),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("session_start", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("session_end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("max_rounds", sa.Integer(), nullable=True),
        sa.Column("carrier_offer", sa.NUMERIC(precision=10, scale=2), nullable=False),
        sa.Column("system_response", sa.String(length=50), nullable=False),
        sa.Column("counter_offer", sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column("loadboard_rate", sa.NUMERIC(precision=10, scale=2), nullable=False),
        sa.Column(
            "minimum_acceptable", sa.NUMERIC(precision=10, scale=2), nullable=True
        ),
        sa.Column(
            "maximum_acceptable", sa.NUMERIC(precision=10, scale=2), nullable=True
        ),
        sa.Column(
            "decision_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("message_to_carrier", sa.Text(), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("final_status", sa.String(length=30), nullable=True),
        sa.Column("agreed_rate", sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column("response_time_seconds", sa.Integer(), nullable=True),
        sa.Column("total_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["call_id"],
            ["calls.call_id"],
        ),
        sa.ForeignKeyConstraint(
            ["carrier_id"],
            ["carriers.carrier_id"],
        ),
        sa.ForeignKeyConstraint(
            ["load_id"],
            ["loads.load_id"],
        ),
        sa.PrimaryKeyConstraint("negotiation_id"),
    )
    op.create_index(
        op.f("ix_negotiations_call_id"), "negotiations", ["call_id"], unique=False
    )
    op.create_index(
        op.f("ix_negotiations_load_id"), "negotiations", ["load_id"], unique=False
    )
    op.create_index(
        op.f("ix_negotiations_carrier_id"), "negotiations", ["carrier_id"], unique=False
    )
    op.create_index(
        op.f("ix_negotiations_session_id"), "negotiations", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_negotiations_is_active"), "negotiations", ["is_active"], unique=False
    )
    op.create_index(
        op.f("ix_negotiations_round_number"),
        "negotiations",
        ["round_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_negotiations_final_status"),
        "negotiations",
        ["final_status"],
        unique=False,
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table("negotiations")
    op.drop_table("calls")
    op.drop_table("loads")
    op.drop_table("carriers")
