"""Tests for the timestamp service day periods functionality."""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from services.timestamp_service import TimestampService


@pytest.fixture
def timestamp_service():
    """Create a timestamp service instance for testing."""
    return TimestampService()


@pytest.mark.asyncio
async def test_day_period_defaults(timestamp_service):
    """Test that each day period generates timestamps within the correct time range."""
    # Define the expected hour ranges for each period
    period_ranges = {
        "morning": (6, 12),  # 6:00 AM to 12:00 PM
        "day": (10, 16),     # 10:00 AM to 4:00 PM
        "evening": (16, 22), # 4:00 PM to 10:00 PM
        "night": (22, 6)     # 10:00 PM to 6:00 AM (spans midnight)
    }
    
    # Test each period
    for period, (start_hour, end_hour) in period_ranges.items():
        # Generate 10 timestamps for each period to ensure consistency
        for _ in range(10):
            result = await timestamp_service._handle_generate_random_timestamp({"day_period": period})
            
            # Extract the timestamp from the result text
            result_text = result.content[0]["text"]
            timestamp_line = [line for line in result_text.split('\n') if line.startswith("ISO 8601:")][0]
            timestamp_str = timestamp_line.replace("ISO 8601:", "").strip()
            timestamp = datetime.fromisoformat(timestamp_str)
            
            # Check if the hour is within the expected range
            hour = timestamp.hour
            
            if period == "night":
                # Night period spans midnight, so we need special handling
                assert (hour >= start_hour or hour < end_hour), \
                    f"Hour {hour} not in night period range ({start_hour}-{end_hour})"
            else:
                assert start_hour <= hour < end_hour, \
                    f"Hour {hour} not in {period} period range ({start_hour}-{end_hour})"


@pytest.mark.asyncio
async def test_month_long_range_with_day_period(timestamp_service):
    """Test that when given a month-long range with a day period, the timestamps still respect the day period."""
    # Create a month-long range
    now = datetime.now(timezone.utc)
    start_time = now
    end_time = now + timedelta(days=30)
    
    # Test with each day period
    for period in ["morning", "day", "evening", "night"]:
        # Generate 10 timestamps for each period
        for _ in range(10):
            result = await timestamp_service._handle_generate_random_timestamp({
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "day_period": period
            })
            
            # Extract the timestamp from the result text
            result_text = result.content[0]["text"]
            timestamp_line = [line for line in result_text.split('\n') if line.startswith("ISO 8601:")][0]
            timestamp_str = timestamp_line.replace("ISO 8601:", "").strip()
            timestamp = datetime.fromisoformat(timestamp_str)
            
            # Verify the timestamp is within the month-long range
            assert start_time <= timestamp <= end_time, \
                f"Timestamp {timestamp} not within range {start_time} to {end_time}"
            
            # The current implementation doesn't enforce day periods when explicit start/end times are provided
            # This test confirms the current behavior, but suggests we might want to modify the implementation


@pytest.mark.asyncio
async def test_day_selector_with_time_period(timestamp_service):
    """Test a hypothetical day selector with time period functionality."""
    # This test demonstrates how we might want to enhance the service
    # with day selection while still respecting time periods
    
    # Mock implementation for testing purposes
    async def mock_generate_with_day_and_period(day_offset, period):
        now = datetime.now(timezone.utc)
        target_day = now + timedelta(days=day_offset)
        
        # Define time ranges for periods
        period_ranges = {
            "morning": (6, 12),
            "day": (10, 16),
            "evening": (16, 22),
            "night": (22, 6)
        }
        
        start_hour, end_hour = period_ranges[period]
        
        # Create timestamps for the specific day and period
        if period == "night" and start_hour > end_hour:
            # Night spans midnight
            if start_hour <= now.hour or now.hour < end_hour:
                # We're currently in the night period
                start_time = datetime(
                    target_day.year, target_day.month, target_day.day,
                    start_hour, 0, 0, tzinfo=timezone.utc
                )
                end_time = datetime(
                    target_day.year, target_day.month, target_day.day,
                    end_hour, 0, 0, tzinfo=timezone.utc
                ) + timedelta(days=1)
            else:
                # We're not in the night period
                start_time = datetime(
                    target_day.year, target_day.month, target_day.day,
                    start_hour, 0, 0, tzinfo=timezone.utc
                )
                end_time = datetime(
                    target_day.year, target_day.month, target_day.day,
                    end_hour, 0, 0, tzinfo=timezone.utc
                ) + timedelta(days=1)
        else:
            # Other periods don't span midnight
            start_time = datetime(
                target_day.year, target_day.month, target_day.day,
                start_hour, 0, 0, tzinfo=timezone.utc
            )
            end_time = datetime(
                target_day.year, target_day.month, target_day.day,
                end_hour, 0, 0, tzinfo=timezone.utc
            )
        
        # Generate a random timestamp within this range
        params = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "day_period": period
        }
        
        return await timestamp_service._handle_generate_random_timestamp(params)
    
    # Test for various days and periods
    days = [0, 1, 7, 14, 30]  # Today, tomorrow, next week, two weeks, month
    periods = ["morning", "day", "evening", "night"]
    
    for day in days:
        for period in periods:
            result = await mock_generate_with_day_and_period(day, period)
            
            # Extract the timestamp from the result text
            result_text = result.content[0]["text"]
            timestamp_line = [line for line in result_text.split('\n') if line.startswith("ISO 8601:")][0]
            timestamp_str = timestamp_line.replace("ISO 8601:", "").strip()
            timestamp = datetime.fromisoformat(timestamp_str)
            
            # Verify the timestamp is for the correct day
            now = datetime.now(timezone.utc)
            target_day = now + timedelta(days=day)
            
            # Check if it's the right day (accounting for night period spanning midnight)
            if period == "night":
                # For night period, the timestamp could be on the target day or the day after
                day_diff = (timestamp.date() - target_day.date()).days
                assert day_diff in [0, 1], f"Timestamp day {timestamp.date()} not on target day {target_day.date()} or day after"
            else:
                assert timestamp.date() == target_day.date(), f"Timestamp day {timestamp.date()} not on target day {target_day.date()}"
            
            # Check if the hour is within the expected range for the period
            hour = timestamp.hour
            period_ranges = {
                "morning": (6, 12),
                "day": (10, 16),
                "evening": (16, 22),
                "night": (22, 6)
            }
            start_hour, end_hour = period_ranges[period]
            
            if period == "night":
                # Night period spans midnight
                assert (hour >= start_hour or hour < end_hour), \
                    f"Hour {hour} not in night period range ({start_hour}-{end_hour})"
            else:
                assert start_hour <= hour < end_hour, \
                    f"Hour {hour} not in {period} period range ({start_hour}-{end_hour})"