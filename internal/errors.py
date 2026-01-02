"""Custom errors with tracking IDs."""

from utils.timestamp import format_timestamp
from utils.ksuid import generate_ksuid


class BaseSimError(Exception):
    """Base error with unique ID and timestamp for tracking."""
    
    def __init__(self, message, context=None, cause=None):
        super().__init__(message)
        self.error_id = generate_ksuid()
        self.timestamp = format_timestamp()
        self.context = context or {}
        self.cause = cause
    
    def __str__(self):
        return f"[{self.error_id}] {super().__str__()}"


class BusError(BaseSimError):
    """Event bus errors (subscribe/publish failures)."""
    
    def __init__(self, message, subscriber_name=None, **kwargs):
        context = kwargs.pop("context", {})
        if subscriber_name:
            context["subscriber_name"] = subscriber_name
        super().__init__(message, context=context, **kwargs)


class HealthCheckError(BaseSimError):
    """Health check failures."""
    
    def __init__(self, message, component=None, **kwargs):
        context = kwargs.pop("context", {})
        if component:
            context["component"] = component
        super().__init__(message, context=context, **kwargs)

