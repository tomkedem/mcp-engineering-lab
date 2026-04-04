import json
import logging


class SafeLogger:
    """
    A wrapper around Python's standard logger that automatically
    redacts sensitive fields before writing to the log.

    Sensitive data such as passwords, tokens, and API keys must never
    appear in logs. This logger enforces that rule at the logging layer
    rather than relying on callers to remember to redact manually.

    Usage:
        logger = SafeLogger("mcp_server")
        logger.info("Tool called", extra={"tool": "search", "token": "abc"})
        # Output: Tool called | {"tool": "search", "token": "[REDACTED]"}
    """

    # Fields that will always be redacted regardless of their value
    SENSITIVE_FIELDS = {
        "password",
        "token",
        "api_key",
        "secret",
        "card_number",
        "credentials",
        "authorization",
        "private_key",
        "access_token",
        "refresh_token"
    }

    def __init__(self, name: str):
        """
        Initializes the logger with a stream handler and INFO level.
        The name should reflect the component using the logger.
        """
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _redact(self, data: dict) -> dict:
        """
        Recursively redacts sensitive fields from a dictionary.
        Handles nested dictionaries by redacting at all levels.
        Non-dict values are returned unchanged.
        """
        if not isinstance(data, dict):
            return data
        return {
            k: "[REDACTED]" if k.lower() in self.SENSITIVE_FIELDS
            else self._redact(v) if isinstance(v, dict)
            else v
            for k, v in data.items()
        }

    def _format(self, message: str, extra: dict) -> str:
        """
        Formats a log message with redacted extra fields as JSON.
        """
        safe_extra = self._redact(extra or {})
        return f"{message} | {json.dumps(safe_extra)}"

    def info(self, message: str, extra: dict = None):
        """Logs an informational message with redacted extra fields."""
        self.logger.info(self._format(message, extra))

    def warning(self, message: str, extra: dict = None):
        """Logs a warning message with redacted extra fields."""
        self.logger.warning(self._format(message, extra))

    def error(self, message: str, extra: dict = None):
        """Logs an error message with redacted extra fields."""
        self.logger.error(self._format(message, extra))


# Singleton instance used throughout the application
safe_logger = SafeLogger("mcp_server")
