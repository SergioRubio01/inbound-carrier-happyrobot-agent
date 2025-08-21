"""
File: test_call_metrics_repository.py
Description: Unit tests for CallMetricsRepository
Author: HappyRobot Team
Created: 2025-01-08
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.call_metrics_model import CallMetricsModel
from src.infrastructure.database.postgres.call_metrics_repository import (
    PostgresCallMetricsRepository,
)


@pytest.fixture
def mock_session():
    """Mock AsyncSession fixture."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def repository(mock_session):
    """CallMetricsRepository fixture."""
    return PostgresCallMetricsRepository(mock_session)


@pytest.fixture
def sample_metrics_model():
    """Sample CallMetricsModel fixture."""
    return CallMetricsModel(
        metrics_id=uuid4(),
        transcript="Test transcript",
        response="ACCEPTED",
        reason="Test reason",
        final_loadboard_rate=2500.00,
        session_id="test-session-123",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_metrics_success(repository, mock_session, sample_metrics_model):
    """Test successful metrics creation."""
    # Mock the create method to return the model
    with patch.object(repository, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = sample_metrics_model

        result = await repository.create_metrics(
            transcript="Test transcript",
            response="ACCEPTED",
            reason="Test reason",
            final_loadboard_rate=2500.00,
            session_id="test-session-123",
        )

        # Verify create was called
        mock_create.assert_called_once()

        # Verify the result
        assert result == sample_metrics_model
        assert result.transcript == "Test transcript"
        assert result.response == "ACCEPTED"
        assert result.reason == "Test reason"
        assert result.final_loadboard_rate == 2500.00
        assert result.session_id == "test-session-123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_metrics_minimal_data(repository, mock_session):
    """Test metrics creation with minimal data."""
    minimal_model = CallMetricsModel(
        metrics_id=uuid4(),
        transcript="Minimal transcript",
        response="REJECTED",
        reason=None,
        final_loadboard_rate=None,
        session_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with patch.object(repository, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = minimal_model

        result = await repository.create_metrics(
            transcript="Minimal transcript",
            response="REJECTED",
        )

        mock_create.assert_called_once()
        assert result.reason is None
        assert result.final_loadboard_rate is None
        assert result.session_id is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_metrics_by_id_found(repository, mock_session, sample_metrics_model):
    """Test getting metrics by ID when found."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_metrics_model
    mock_session.execute.return_value = mock_result

    result = await repository.get_metrics_by_id(sample_metrics_model.metrics_id)

    assert result == sample_metrics_model
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_metrics_by_id_not_found(repository, mock_session):
    """Test getting metrics by ID when not found."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await repository.get_metrics_by_id(uuid4())

    assert result is None
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_metrics_with_date_filters(
    repository, mock_session, sample_metrics_model
):
    """Test getting metrics with date filters."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_metrics_model]
    mock_session.execute.return_value = mock_result

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    result = await repository.get_metrics(
        start_date=start_date,
        end_date=end_date,
        limit=50,
        offset=0,
    )

    assert len(result) == 1
    assert result[0] == sample_metrics_model
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_metrics_without_filters(
    repository, mock_session, sample_metrics_model
):
    """Test getting metrics without date filters."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_metrics_model]
    mock_session.execute.return_value = mock_result

    result = await repository.get_metrics()

    assert len(result) == 1
    assert result[0] == sample_metrics_model
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_metrics_summary_with_data(repository, mock_session):
    """Test getting metrics summary with sample data."""
    # Mock total count query
    mock_total_result = MagicMock()
    mock_total_result.scalar.return_value = 100

    # Mock response distribution query
    mock_response_result = MagicMock()
    mock_response_result.fetchall.return_value = [("ACCEPTED", 60), ("REJECTED", 40)]

    # Mock average rate query
    mock_avg_result = MagicMock()
    mock_avg_result.scalar.return_value = 2450.50

    # Mock rejection reasons query
    mock_rejection_result = MagicMock()
    mock_rejection_result.fetchall.return_value = [
        ("Rate too high", 25),
        ("Equipment mismatch", 15),
    ]

    # Set up the execute calls to return the right mocks in sequence
    mock_session.execute.side_effect = [
        mock_total_result,
        mock_response_result,
        mock_avg_result,
        mock_rejection_result,
    ]

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    result = await repository.get_metrics_summary(
        start_date=start_date, end_date=end_date
    )

    assert result["total_calls"] == 100
    assert result["acceptance_rate"] == 0.6  # 60/100
    assert result["average_final_rate"] == 2450.50
    assert result["response_distribution"] == {"ACCEPTED": 60, "REJECTED": 40}
    assert len(result["top_rejection_reasons"]) == 2
    assert result["top_rejection_reasons"][0]["reason"] == "Rate too high"
    assert result["top_rejection_reasons"][0]["count"] == 25
    assert result["period"]["start"] == start_date.isoformat()
    assert result["period"]["end"] == end_date.isoformat()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_metrics_summary_no_data(repository, mock_session):
    """Test getting metrics summary with no data."""
    # Mock all queries to return zero/empty results
    mock_empty_result = MagicMock()
    mock_empty_result.scalar.return_value = 0
    mock_empty_result.fetchall.return_value = []

    mock_session.execute.return_value = mock_empty_result

    result = await repository.get_metrics_summary()

    assert result["total_calls"] == 0
    assert result["acceptance_rate"] == 0.0
    assert result["average_final_rate"] == 0.0
    assert result["response_distribution"] == {}
    assert result["top_rejection_reasons"] == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_exists_true(repository, mock_session):
    """Test exists method returns True when record exists."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    mock_session.execute.return_value = mock_result

    result = await repository.exists(uuid4())

    assert result is True
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_exists_false(repository, mock_session):
    """Test exists method returns False when record doesn't exist."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_session.execute.return_value = mock_result

    result = await repository.exists(uuid4())

    assert result is False
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_success(repository, mock_session, sample_metrics_model):
    """Test successful deletion."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_metrics_model
    mock_session.execute.return_value = mock_result

    result = await repository.delete(sample_metrics_model.metrics_id)

    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.delete.assert_called_once_with(sample_metrics_model)
    mock_session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_not_found(repository, mock_session):
    """Test deletion when record not found."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await repository.delete(uuid4())

    assert result is False
    mock_session.delete.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_metrics_by_session_id(
    repository, mock_session, sample_metrics_model
):
    """Test getting metrics by session ID."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_metrics_model]
    mock_session.execute.return_value = mock_result

    result = await repository.get_metrics_by_session_id("test-session-123")

    assert len(result) == 1
    assert result[0] == sample_metrics_model
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_metrics_with_filters(repository, mock_session):
    """Test counting metrics with date filters."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = 42
    mock_session.execute.return_value = mock_result

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    result = await repository.count_metrics(start_date=start_date, end_date=end_date)

    assert result == 42
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_metrics_without_filters(repository, mock_session):
    """Test counting metrics without filters."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = 100
    mock_session.execute.return_value = mock_result

    result = await repository.count_metrics()

    assert result == 100
    mock_session.execute.assert_called_once()


# Additional DELETE-specific tests for comprehensive coverage


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_existing_metrics(repository, mock_session, sample_metrics_model):
    """Test deleting existing metrics returns True."""
    # Mock the create method to return the model
    with patch.object(
        repository, "create_metrics", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = sample_metrics_model

        # Create a metric
        created = await repository.create_metrics(
            transcript="Test", response="ACCEPTED"
        )

        # Mock the delete query to find the record
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_metrics_model
        mock_session.execute.return_value = mock_result

        # Delete it
        result = await repository.delete(created.metrics_id)
        assert result is True

        # Verify delete and flush were called
        mock_session.delete.assert_called_once_with(sample_metrics_model)
        mock_session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_nonexistent_metrics(repository, mock_session):
    """Test deleting non-existent metrics returns False."""
    fake_id = uuid4()

    # Mock the query to return None (record not found)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await repository.delete(fake_id)
    assert result is False

    # Verify delete was not called
    mock_session.delete.assert_not_called()
    mock_session.flush.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_exists_method_comprehensive(
    repository, mock_session, sample_metrics_model
):
    """Test exists method works correctly for various scenarios."""
    # Test when record exists
    mock_result_exists = MagicMock()
    mock_result_exists.scalar.return_value = 1

    # Test when record doesn't exist
    mock_result_not_exists = MagicMock()
    mock_result_not_exists.scalar.return_value = 0

    # First call - record exists
    mock_session.execute.return_value = mock_result_exists
    assert await repository.exists(sample_metrics_model.metrics_id) is True

    # Second call - record doesn't exist
    mock_session.execute.return_value = mock_result_not_exists
    assert await repository.exists(uuid4()) is False

    # Verify execute was called twice
    assert mock_session.execute.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_transaction_integrity(
    repository, mock_session, sample_metrics_model
):
    """Test delete operation maintains transaction integrity."""
    # Mock successful find
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_metrics_model
    mock_session.execute.return_value = mock_result

    # Delete the record
    result = await repository.delete(sample_metrics_model.metrics_id)

    # Verify the sequence of operations
    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.delete.assert_called_once_with(sample_metrics_model)
    mock_session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_with_database_exception(
    repository, mock_session, sample_metrics_model
):
    """Test delete method handles database exceptions properly."""
    # Mock the query to find the record
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_metrics_model
    mock_session.execute.return_value = mock_result

    # Mock delete to raise an exception
    mock_session.delete.side_effect = Exception("Database error")

    # The delete method should propagate the exception
    with pytest.raises(Exception) as exc_info:
        await repository.delete(sample_metrics_model.metrics_id)

    assert str(exc_info.value) == "Database error"
    mock_session.delete.assert_called_once_with(sample_metrics_model)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_and_exists_integration(
    repository, mock_session, sample_metrics_model
):
    """Test integration between delete and exists methods."""
    metrics_id = sample_metrics_model.metrics_id

    # Test 1: Record exists
    mock_exists_result = MagicMock()
    mock_exists_result.scalar.return_value = 1
    mock_session.execute.return_value = mock_exists_result

    exists_before = await repository.exists(metrics_id)
    assert exists_before is True

    # Test 2: Delete the record
    mock_delete_result = MagicMock()
    mock_delete_result.scalar_one_or_none.return_value = sample_metrics_model
    mock_session.execute.return_value = mock_delete_result

    delete_result = await repository.delete(metrics_id)
    assert delete_result is True

    # Test 3: Record no longer exists
    mock_not_exists_result = MagicMock()
    mock_not_exists_result.scalar.return_value = 0
    mock_session.execute.return_value = mock_not_exists_result

    exists_after = await repository.exists(metrics_id)
    assert exists_after is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_query_construction(
    repository, mock_session, sample_metrics_model
):
    """Test that delete method constructs proper SQL query."""

    # Mock the query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_metrics_model
    mock_session.execute.return_value = mock_result

    await repository.delete(sample_metrics_model.metrics_id)

    # Verify execute was called with the correct query structure
    mock_session.execute.assert_called_once()

    # Get the call arguments
    call_args = mock_session.execute.call_args[0]
    assert len(call_args) == 1

    # The query should be a Select statement
    query = call_args[0]
    assert hasattr(query, "whereclause")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_uuid_type_handling(repository, mock_session):
    """Test delete method properly handles UUID types."""
    from uuid import UUID

    # Test with UUID object
    uuid_obj = uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await repository.delete(uuid_obj)
    assert result is False

    # Verify execute was called
    mock_session.execute.assert_called_once()

    # Test that the method accepts UUID type
    assert isinstance(uuid_obj, UUID)
