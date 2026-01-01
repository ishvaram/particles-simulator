"""Microsecond timestamp utilities."""

import time
from datetime import datetime, timezone


def now_micros():
    """Current time in microseconds since Unix epoch."""
    return int(time.time() * 1_000_000)


def format_timestamp(epoch_us=None):
    """Format timestamp as ISO 8601 with microseconds."""
    if epoch_us is None:
        epoch_us = now_micros()
    
    dt = datetime.fromtimestamp(epoch_us / 1_000_000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
