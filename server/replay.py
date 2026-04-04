import datetime
import json
import uuid

from server.security import sanitize_for_audit


class ReplayStore:
    """
    Records tool calls in a structured format that allows exact replay.

    When a production failure occurs, the Replay Store allows developers
    to export the exact sequence of tool calls that led to the failure
    and reproduce it in a development environment with full logging.

    Key design decisions:
    - Arguments are sanitized before storage to prevent sensitive data
      from accumulating in the replay store.
    - Results are truncated to 200 characters to avoid storing large
      amounts of user data unnecessarily.
    - In production, replace the in-memory list with a persistent store
      such as a database or object storage with a defined retention policy.

    Usage:
        replay_store.record(tool_name, arguments, result, is_error, corr_id)
        exported = replay_store.export_for_replay(correlation_id)
    """

    def __init__(self):
        # In-memory storage for development and testing.
        # Replace with persistent storage in production.
        self.recordings = []

    def record(
        self,
        tool_name: str,
        arguments: dict,
        result: str,
        is_error: bool,
        correlation_id: str
    ):
        """
        Records a single tool call for potential replay.

        Called in the finally block of every tool execution to ensure
        recording happens regardless of success or failure.

        Arguments are sanitized to remove sensitive fields before storage.
        Results are truncated to prevent accumulation of large payloads.
        """
        self.recordings.append({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
            "tool_name": tool_name,

            # Sanitized to remove sensitive fields before storage
            "arguments": sanitize_for_audit(arguments),

            # Truncated to avoid storing large user data payloads
            "result_summary": result[:200] if result else "",

            "is_error": is_error
        })

    def get_by_correlation_id(self, correlation_id: str) -> list:
        """
        Returns all recorded tool calls for a specific request.

        Use the Correlation ID from the logs to identify the request
        you want to replay.
        """
        return [
            r for r in self.recordings
            if r["correlation_id"] == correlation_id
        ]

    def export_for_replay(self, correlation_id: str) -> str:
        """
        Exports a recorded request as a JSON string for replay.

        The exported JSON contains the full sequence of tool calls
        for the given Correlation ID. Save it to a file and use
        replay_from_file() to reproduce the failure in development.

        Returns a JSON string with the following structure:
        {
            "correlation_id": "...",
            "exported_at": "...",
            "tool_calls": [...]
        }
        """
        calls = self.get_by_correlation_id(correlation_id)
        return json.dumps({
            "correlation_id": correlation_id,
            "exported_at": datetime.datetime.utcnow().isoformat(),
            "tool_calls": calls
        }, indent=2)

    def replay_from_file(self, filepath: str) -> list:
        """
        Loads a previously exported recording from a JSON file.

        Use this to reproduce a production failure in development.
        Returns the list of tool calls in the recording.

        Example:
            calls = replay_store.replay_from_file("failure-20260115.json")
            for call in calls:
                print(call["tool_name"], call["arguments"])
        """
        with open(filepath) as f:
            recording = json.load(f)

        return recording.get("tool_calls", [])


# Singleton instance used throughout the application
replay_store = ReplayStore()
