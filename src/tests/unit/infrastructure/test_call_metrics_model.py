"""
File: test_call_metrics_model.py
Description: Unit tests for CallMetricsModel
Author: HappyRobot Team
Created: 2025-01-08
"""

from uuid import UUID, uuid4

import pytest

from src.infrastructure.database.models.call_metrics_model import CallMetricsModel


@pytest.mark.unit
def test_call_metrics_model_creation():
    """Test CallMetricsModel creation with all fields."""
    metrics_id = uuid4()
    transcript = "Test conversation transcript"
    response = "ACCEPTED"
    reason = "Rate was acceptable"
    final_rate = 2500.00
    session_id = "session-123"

    metrics = CallMetricsModel(
        metrics_id=metrics_id,
        transcript=transcript,
        response=response,
        reason=reason,
        final_loadboard_rate=final_rate,
        session_id=session_id,
    )

    assert metrics.metrics_id == metrics_id
    assert metrics.transcript == transcript
    assert metrics.response == response
    assert metrics.reason == reason
    assert metrics.final_loadboard_rate == final_rate
    assert metrics.session_id == session_id


@pytest.mark.unit
def test_call_metrics_model_minimal_creation():
    """Test CallMetricsModel creation with minimal required fields."""
    transcript = "Minimal transcript"
    response = "REJECTED"

    metrics = CallMetricsModel(
        transcript=transcript,
        response=response,
    )

    # Should auto-generate UUID for metrics_id
    assert isinstance(metrics.metrics_id, UUID)
    assert metrics.transcript == transcript
    assert metrics.response == response
    assert metrics.reason is None
    assert metrics.final_loadboard_rate is None
    assert metrics.session_id is None


@pytest.mark.unit
def test_call_metrics_model_repr():
    """Test CallMetricsModel string representation."""
    metrics_id = uuid4()
    metrics = CallMetricsModel(
        metrics_id=metrics_id,
        transcript="Test transcript",
        response="ACCEPTED",
        session_id="session-123",
    )

    repr_str = repr(metrics)

    assert "CallMetricsModel" in repr_str
    assert str(metrics_id) in repr_str
    assert "ACCEPTED" in repr_str
    assert "session-123" in repr_str


@pytest.mark.unit
def test_call_metrics_model_table_name():
    """Test that the table name is correctly set."""
    assert CallMetricsModel.__tablename__ == "call_metrics"


@pytest.mark.unit
def test_call_metrics_model_nullable_constraints():
    """Test nullable/not-nullable constraints."""
    # This test ensures the model structure is correct
    metrics = CallMetricsModel(
        transcript="Required transcript",
        response="REQUIRED",
        reason=None,  # Should be nullable
        final_loadboard_rate=None,  # Should be nullable
        session_id=None,  # Should be nullable
    )

    assert metrics.transcript is not None
    assert metrics.response is not None
    assert metrics.reason is None
    assert metrics.final_loadboard_rate is None
    assert metrics.session_id is None


@pytest.mark.unit
def test_call_metrics_model_with_timestamp_mixin():
    """Test that TimestampMixin fields are available."""
    metrics = CallMetricsModel(
        transcript="Test transcript",
        response="ACCEPTED",
    )

    # These fields should be available due to TimestampMixin
    # They will be None until saved to database
    assert hasattr(metrics, "created_at")
    assert hasattr(metrics, "updated_at")


@pytest.mark.unit
def test_call_metrics_model_numeric_precision():
    """Test numeric field precision for final_loadboard_rate."""
    # Test with various numeric values
    test_rates = [0.00, 999.99, 1234.56, 99999999.99]

    for rate in test_rates:
        metrics = CallMetricsModel(
            transcript="Test transcript",
            response="ACCEPTED",
            final_loadboard_rate=rate,
        )
        assert metrics.final_loadboard_rate == rate


@pytest.mark.unit
def test_call_metrics_model_response_length():
    """Test response field length constraint (max 50 chars)."""
    # Test with exactly 50 characters
    long_response = "A" * 50

    metrics = CallMetricsModel(
        transcript="Test transcript",
        response=long_response,
    )

    assert len(metrics.response) == 50
    assert metrics.response == long_response


@pytest.mark.unit
def test_call_metrics_model_session_id_length():
    """Test session_id field length constraint (max 100 chars)."""
    # Test with exactly 100 characters
    long_session_id = "S" * 100

    metrics = CallMetricsModel(
        transcript="Test transcript",
        response="ACCEPTED",
        session_id=long_session_id,
    )

    assert len(metrics.session_id) == 100
    assert metrics.session_id == long_session_id


@pytest.mark.unit
def test_call_metrics_model_uuid_generation():
    """Test that UUID is auto-generated when not provided."""
    metrics1 = CallMetricsModel(
        transcript="Test transcript 1",
        response="ACCEPTED",
    )

    metrics2 = CallMetricsModel(
        transcript="Test transcript 2",
        response="REJECTED",
    )

    # Should auto-generate different UUIDs
    assert isinstance(metrics1.metrics_id, UUID)
    assert isinstance(metrics2.metrics_id, UUID)
    assert metrics1.metrics_id != metrics2.metrics_id


@pytest.mark.unit
def test_call_metrics_model_various_response_types():
    """Test model with various response types."""
    response_types = [
        "ACCEPTED",
        "REJECTED",
        "ABANDONED",
        "TRANSFER",
        "ERROR",
        "TIMEOUT",
        "DISCONNECTED",
    ]

    for response_type in response_types:
        metrics = CallMetricsModel(
            transcript=f"Transcript for {response_type}",
            response=response_type,
            reason=f"Reason for {response_type}",
        )

        assert metrics.response == response_type
        assert metrics.reason == f"Reason for {response_type}"
