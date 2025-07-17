"""Helper functions for testing."""

from datetime import datetime

# Fixed datetime for testing
FIXED_DATETIME = datetime(2023, 1, 1, 12, 0)

# Mock datetime.now function
def mock_datetime_now():
    return FIXED_DATETIME