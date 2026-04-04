import os


class Config:
    """
    Central configuration for the MCP server.
    All settings are loaded from environment variables.
    Defaults are suitable for development only.
    Production requires explicit values for all sensitive settings.
    """

    # Runtime environment: development, staging, production
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

    # HTTP port for the server (used by server_http.py)
    PORT = int(os.environ.get("PORT", 8080))

    # Logging verbosity: DEBUG, INFO, WARNING, ERROR
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Maximum wait time for database queries before timeout
    DATABASE_TIMEOUT_SECONDS = float(
        os.environ.get("DATABASE_TIMEOUT_SECONDS", 5.0)
    )

    # Maximum number of tool calls allowed per user per minute
    MAX_REQUESTS_PER_MINUTE = int(
        os.environ.get("MAX_REQUESTS_PER_MINUTE", 100)
    )

    @classmethod
    def validate_production(cls):
        """
        Validates that all required production settings are configured.
        Called at server startup to fail fast if configuration is incomplete.
        Raises RuntimeError if any required variable is missing.
        """
        if cls.ENVIRONMENT == "production":
            required = ["DATABASE_PASSWORD", "API_KEY", "REDIS_URL"]
            missing = [var for var in required if not os.environ.get(var)]
            if missing:
                raise RuntimeError(
                    f"Missing required environment variables for production: {missing}"
                )


# Singleton instance used throughout the application
config = Config()
