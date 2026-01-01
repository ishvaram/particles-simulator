"""Crash handling utilities."""

import json
import os
import sys
import traceback

from utils.ksuid import generate_ksuid
from utils.timestamp import format_timestamp

# Default crash log path, can be overridden by configure()
_crash_log = "logs/crash.log"


def configure(crash_file):
    """Set crash log file path from config."""
    global _crash_log
    _crash_log = crash_file


def _write_crash(crash_id, timestamp, exc_name, exc_msg, tb, context=None):
    """Write crash to file. Never raises."""
    try:
        log_dir = os.path.dirname(_crash_log)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        record = {"id": crash_id, "timestamp": timestamp, "type": exc_name, "msg": exc_msg, "traceback": tb}
        if context:
            record["context"] = context
        with open(_crash_log, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def log_crash(exc_type, exc_value, exc_tb):
    """Log sync crash to stderr and file. Never raises."""
    crash_id = generate_ksuid()
    timestamp = format_timestamp()
    exc_name = exc_type.__name__ if exc_type else "Unknown"
    exc_msg = str(exc_value) if exc_value else ""
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    
    sys.stderr.write(f"\n{'=' * 60}\nCRASH [{crash_id}] {timestamp}\n{'=' * 60}\n")
    sys.stderr.write(f"{exc_name}: {exc_msg}\n{'-' * 60}\n{tb}{'=' * 60}\n\n")
    _write_crash(crash_id, timestamp, exc_name, exc_msg, tb)


def log_async_crash(exc, context_dict, logger=None):
    """Log async task crash. Never raises."""
    crash_id = generate_ksuid()
    timestamp = format_timestamp()
    exc_name = type(exc).__name__ if exc else "AsyncError"
    exc_msg = str(exc) if exc else context_dict.get("message", "Unknown")
    tb = traceback.format_exc() if exc else None
    
    if logger:
        logger.error("Async exception", error=exc_msg, task=str(context_dict.get("future", "unknown")))
    
    _write_crash(crash_id, timestamp, exc_name, exc_msg, tb, str(context_dict))


def create_async_handler(logger=None):
    """Create async exception handler for event loop."""
    def handler(loop, context):
        log_async_crash(context.get("exception"), context, logger)
    return handler


def install_crash_handler():
    """Install global sync exception handler."""
    sys.excepthook = log_crash
