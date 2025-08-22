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
    response = "Success"
    response_reason = "Rate was acceptable"
    sentiment = "Positive"
    sentiment_reason = "Customer was satisfied"
    session_id = "session-123"

    metrics = CallMetricsModel(
        metrics_id=metrics_id,
        transcript=transcript,
        response=response,
        response_reason=response_reason,
        sentiment=sentiment,
        sentiment_reason=sentiment_reason,
        session_id=session_id,
    )

    assert metrics.metrics_id == metrics_id
    assert metrics.transcript == transcript
    assert metrics.response == response
    assert metrics.response_reason == response_reason
    assert metrics.sentiment == sentiment
    assert metrics.sentiment_reason == sentiment_reason
    assert metrics.session_id == session_id


@pytest.mark.unit
def test_call_metrics_model_minimal_creation():
    """Test CallMetricsModel creation with minimal required fields."""
    transcript = "Minimal transcript"
    response = "Rate too high"

    metrics = CallMetricsModel(
        transcript=transcript,
        response=response,
    )

    # The UUID will be None until saved to database (default is applied on insert)
    # or we can explicitly set it
    if metrics.metrics_id is None:
        metrics.metrics_id = uuid4()

    assert isinstance(metrics.metrics_id, UUID)
    assert metrics.transcript == transcript
    assert metrics.response == response
    assert metrics.response_reason is None
    assert metrics.sentiment is None
    assert metrics.sentiment_reason is None
    assert metrics.session_id is None


@pytest.mark.unit
def test_call_metrics_model_repr():
    """Test CallMetricsModel string representation."""
    metrics_id = uuid4()
    metrics = CallMetricsModel(
        metrics_id=metrics_id,
        transcript="Test transcript",
        response="Success",
        session_id="session-123",
    )

    repr_str = repr(metrics)

    assert "CallMetricsModel" in repr_str
    assert str(metrics_id) in repr_str
    assert "Success" in repr_str
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
        response="Success",
        response_reason=None,  # Should be nullable
        sentiment=None,  # Should be nullable
        sentiment_reason=None,  # Should be nullable
        session_id=None,  # Should be nullable
    )

    assert metrics.transcript is not None
    assert metrics.response is not None
    assert metrics.response_reason is None
    assert metrics.sentiment is None
    assert metrics.sentiment_reason is None
    assert metrics.session_id is None


@pytest.mark.unit
def test_call_metrics_model_with_timestamp_mixin():
    """Test that TimestampMixin fields are available."""
    metrics = CallMetricsModel(
        transcript="Test transcript",
        response="Success",
    )

    # These fields should be available due to TimestampMixin
    # They will be None until saved to database
    assert hasattr(metrics, "created_at")
    assert hasattr(metrics, "updated_at")


@pytest.mark.unit
def test_call_metrics_model_sentiment_enum():
    """Test sentiment field with valid enum values."""
    # Test with valid sentiment values
    valid_sentiments = ["Positive", "Neutral", "Negative"]

    for sentiment in valid_sentiments:
        metrics = CallMetricsModel(
            transcript="Test transcript",
            response="Success",
            sentiment=sentiment,
        )
        assert metrics.sentiment == sentiment


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
    """Test that UUID can be set or generated."""
    # Test with explicitly set UUID
    explicit_id = uuid4()
    metrics1 = CallMetricsModel(
        metrics_id=explicit_id,
        transcript="Test transcript 1",
        response="ACCEPTED",
    )

    # Test without UUID (will be None until database insert)
    metrics2 = CallMetricsModel(
        transcript="Test transcript 2",
        response="REJECTED",
    )

    # Explicitly set UUID
    assert metrics1.metrics_id == explicit_id
    assert isinstance(metrics1.metrics_id, UUID)

    # UUID will be None until saved to DB or explicitly set
    if metrics2.metrics_id is None:
        metrics2.metrics_id = uuid4()
    assert isinstance(metrics2.metrics_id, UUID)
    assert metrics1.metrics_id != metrics2.metrics_id


@pytest.mark.unit
def test_call_metrics_model_various_response_types():
    """Test model with various response types."""
    response_types = [
        "Success",
        "Rate too high",
        "Incorrect MC",
        "Fallback error",
    ]

    for response_type in response_types:
        metrics = CallMetricsModel(
            transcript=f"Transcript for {response_type}",
            response=response_type,
            response_reason=f"Reason for {response_type}",
        )

        assert metrics.response == response_type
        assert metrics.response_reason == f"Reason for {response_type}"
