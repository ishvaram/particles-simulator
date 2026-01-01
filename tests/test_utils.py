"""Unit tests for utility modules."""

import pytest
from utils.ksuid import generate_ksuid
from utils.timestamp import format_timestamp, now_micros


class TestKSUID:
    """Tests for KSUID generation."""

    def test_generate_ksuid_returns_string(self):
        """KSUID is a string."""
        ksuid = generate_ksuid()
        assert isinstance(ksuid, str)

    def test_generate_ksuid_length(self):
        """KSUID has expected length."""
        ksuid = generate_ksuid()
        assert len(ksuid) == 27  # Base62 encoded

    def test_generate_ksuid_unique(self):
        """KSUIDs are unique."""
        ksuids = [generate_ksuid() for _ in range(100)]
        assert len(set(ksuids)) == 100

    def test_generate_ksuid_sortable(self):
        """KSUIDs are roughly sortable by time."""
        import time
        ksuid1 = generate_ksuid()
        time.sleep(1.1)  # Need >1s for KSUID timestamp to change
        ksuid2 = generate_ksuid()
        # Later KSUID should be >= earlier (lexicographically)
        assert ksuid2 >= ksuid1


class TestTimestamp:
    """Tests for timestamp utilities."""

    def test_format_timestamp_iso_format(self):
        """Timestamp is ISO 8601 format."""
        ts = format_timestamp()
        assert "T" in ts
        assert "Z" in ts or "+" in ts

    def test_format_timestamp_has_microseconds(self):
        """Timestamp includes microseconds."""
        ts = format_timestamp()
        # Should have 6 digits after decimal point
        assert "." in ts
        decimal_part = ts.split(".")[1].split("Z")[0].split("+")[0]
        assert len(decimal_part) == 6

    def test_now_micros_returns_int(self):
        """now_micros returns integer."""
        micros = now_micros()
        assert isinstance(micros, int)

    def test_now_micros_reasonable_value(self):
        """now_micros returns reasonable timestamp."""
        micros = now_micros()
        # Should be after year 2020 in microseconds
        assert micros > 1577836808000000  # 2020-01-01


class TestCrashHandler:
    """Tests for crash handling utilities."""

    def test_configure_sets_path(self):
        """configure() sets crash log path."""
        from utils.crash import configure, _crash_log
        original = _crash_log
        
        configure("/tmp/test_crash.log")
        from utils import crash
        assert crash._crash_log == "/tmp/test_crash.log"
        
        # Restore
        configure(original)

    def test_install_crash_handler(self):
        """install_crash_handler sets sys.excepthook."""
        import sys
        from utils.crash import install_crash_handler, log_crash
        
        original_hook = sys.excepthook
        install_crash_handler()
        
        assert sys.excepthook == log_crash
        
        # Restore
        sys.excepthook = original_hook
