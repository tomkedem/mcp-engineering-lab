import datetime
import uuid


def generate_correlation_id() -> str:
    """
    Generates a unique correlation ID for request tracing.

    The ID combines a timestamp with a short random UUID segment.
    The timestamp prefix makes IDs sortable chronologically,
    which simplifies log filtering and time-based debugging.

    Format: YYYYMMDDHHMMSS-{8 random hex characters}
    Example: 20260115102301-a3f8c2d1

    A new Correlation ID is generated at the start of every request
    that does not already carry one from the Host. The ID is then
    attached to every log entry, metric, and replay record associated
    with that request, making it possible to reconstruct the full
    sequence of events for any given request from the logs alone.

    Usage:
        correlation_id = generate_correlation_id()
        # or, if the request carries one:
        correlation_id = arguments.get("_correlation_id",
                                       generate_correlation_id())
    """
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4()).replace("-", "")[:8]
    return f"{timestamp}-{unique_id}"
