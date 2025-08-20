"""Remove unauthorized load fields for compliance

Revision ID: 004_remove_unauthorized_load_fields
Revises: 79fef0f9887a_add_performance_indexes_for_load_listing
Create Date: 2024-08-20 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "004_remove_load_fields"
down_revision = "79fef0f9887a"
branch_labels = None
depends_on = None


def upgrade():
    """Remove unauthorized fields from loads table to comply with specification."""

    # Drop columns that are not in the allowed list
    with op.batch_alter_table("loads") as batch_op:
        # Drop identity fields
        batch_op.drop_column("external_id")

        # Drop extended location fields
        batch_op.drop_column("origin_coordinates")
        batch_op.drop_column("origin_facility")
        batch_op.drop_column("destination_coordinates")
        batch_op.drop_column("destination_facility")

        # Drop extended schedule fields
        batch_op.drop_column("pickup_time_end")
        batch_op.drop_column("pickup_appointment_required")
        batch_op.drop_column("delivery_time_end")
        batch_op.drop_column("delivery_appointment_required")

        # Drop extended equipment fields
        batch_op.drop_column("equipment_requirements")

        # Drop unauthorized load detail fields
        batch_op.drop_column("pieces")
        batch_op.drop_column("commodity_description")
        batch_op.drop_column("dimensions")
        batch_op.drop_column("hazmat")
        batch_op.drop_column("hazmat_class")

        # Drop distance and route fields
        batch_op.drop_column("miles")
        batch_op.drop_column("estimated_transit_hours")
        batch_op.drop_column("route_notes")

        # Drop extended pricing fields
        batch_op.drop_column("fuel_surcharge")
        batch_op.drop_column("accessorials")

        # Drop negotiation parameters
        batch_op.drop_column("minimum_rate")
        batch_op.drop_column("maximum_rate")
        batch_op.drop_column("target_rate")
        batch_op.drop_column("auto_accept_threshold")

        # Drop broker/customer information
        batch_op.drop_column("broker_company")
        batch_op.drop_column("broker_contact")
        batch_op.drop_column("customer_name")

        # Drop extended status fields
        batch_op.drop_column("status_changed_at")
        batch_op.drop_column("booked_by_carrier_id")
        batch_op.drop_column("booked_at")

        # Drop extended instruction fields
        batch_op.drop_column("special_requirements")
        batch_op.drop_column("internal_notes")

        # Drop urgency and priority fields
        batch_op.drop_column("urgency")
        batch_op.drop_column("priority_score")

        # Drop extended visibility fields
        batch_op.drop_column("expires_at")

        # Drop extended metadata fields
        batch_op.drop_column("source")
        batch_op.drop_column("created_by")
        batch_op.drop_column("deleted_at")


def downgrade():
    """Re-add the columns if rollback is needed."""

    with op.batch_alter_table("loads") as batch_op:
        # Re-add identity fields
        batch_op.add_column(sa.Column("external_id", sa.String(100), nullable=True))

        # Re-add extended location fields
        batch_op.add_column(
            sa.Column("origin_coordinates", postgresql.JSONB, nullable=True)
        )
        batch_op.add_column(
            sa.Column("origin_facility", postgresql.JSONB, nullable=True)
        )
        batch_op.add_column(
            sa.Column("destination_coordinates", postgresql.JSONB, nullable=True)
        )
        batch_op.add_column(
            sa.Column("destination_facility", postgresql.JSONB, nullable=True)
        )

        # Re-add extended schedule fields
        batch_op.add_column(sa.Column("pickup_time_end", sa.Time(), nullable=True))
        batch_op.add_column(
            sa.Column("pickup_appointment_required", sa.Boolean(), default=False)
        )
        batch_op.add_column(sa.Column("delivery_time_end", sa.Time(), nullable=True))
        batch_op.add_column(
            sa.Column("delivery_appointment_required", sa.Boolean(), default=False)
        )

        # Re-add extended equipment fields
        batch_op.add_column(
            sa.Column("equipment_requirements", postgresql.JSONB, nullable=True)
        )

        # Re-add unauthorized load detail fields
        batch_op.add_column(sa.Column("pieces", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("commodity_description", sa.Text(), nullable=True)
        )
        batch_op.add_column(sa.Column("dimensions", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("hazmat", sa.Boolean(), default=False))
        batch_op.add_column(sa.Column("hazmat_class", sa.String(20), nullable=True))

        # Re-add distance and route fields
        batch_op.add_column(
            sa.Column("miles", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("estimated_transit_hours", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("route_notes", sa.Text(), nullable=True))

        # Re-add extended pricing fields
        batch_op.add_column(sa.Column("fuel_surcharge", sa.NUMERIC(10, 2), default=0))
        batch_op.add_column(sa.Column("accessorials", postgresql.JSONB, nullable=True))

        # Re-add negotiation parameters
        batch_op.add_column(sa.Column("minimum_rate", sa.NUMERIC(10, 2), nullable=True))
        batch_op.add_column(sa.Column("maximum_rate", sa.NUMERIC(10, 2), nullable=True))
        batch_op.add_column(sa.Column("target_rate", sa.NUMERIC(10, 2), nullable=True))
        batch_op.add_column(
            sa.Column("auto_accept_threshold", sa.NUMERIC(10, 2), nullable=True)
        )

        # Re-add broker/customer information
        batch_op.add_column(sa.Column("broker_company", sa.String(255), nullable=True))
        batch_op.add_column(
            sa.Column("broker_contact", postgresql.JSONB, nullable=True)
        )
        batch_op.add_column(sa.Column("customer_name", sa.String(255), nullable=True))

        # Re-add extended status fields
        batch_op.add_column(
            sa.Column(
                "status_changed_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.func.now(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "booked_by_carrier_id", postgresql.UUID(as_uuid=True), nullable=True
            )
        )
        batch_op.add_column(
            sa.Column("booked_at", sa.TIMESTAMP(timezone=True), nullable=True)
        )

        # Re-add extended instruction fields
        batch_op.add_column(
            sa.Column(
                "special_requirements", postgresql.ARRAY(sa.Text()), nullable=True
            )
        )
        batch_op.add_column(sa.Column("internal_notes", sa.Text(), nullable=True))

        # Re-add urgency and priority fields
        batch_op.add_column(sa.Column("urgency", sa.String(20), default="NORMAL"))
        batch_op.add_column(sa.Column("priority_score", sa.Integer(), default=50))

        # Re-add extended visibility fields
        batch_op.add_column(
            sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True)
        )

        # Re-add extended metadata fields
        batch_op.add_column(sa.Column("source", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("created_by", sa.String(100), nullable=True))
        batch_op.add_column(
            sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True)
        )
