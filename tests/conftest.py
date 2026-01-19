"""Shared test fixtures and configuration."""

import pytest
from datetime import datetime
from uuid import UUID


@pytest.fixture
def fixed_uuid() -> UUID:
    """Provide a fixed UUID for testing."""
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def fixed_datetime() -> datetime:
    """Provide a fixed datetime for testing."""
    return datetime(2024, 1, 1, 12, 0, 0)
