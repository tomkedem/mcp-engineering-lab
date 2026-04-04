from collections import defaultdict
from server.logging import safe_logger


class MCPMetrics:
    """
    Collects and reports runtime metrics for the MCP server.

    Tracks tool call counts, durations, error rates, validation failures,
    and permission denials per tool. Used for monitoring and alerting.

    In production, replace the in-memory storage with a dedicated
    metrics system such as Prometheus or Datadog.
    """

    def __init__(self):
        # Total number of calls per tool
        self.tool_call_counts = defaultdict(int)

        # List of durations in milliseconds per tool
        self.tool_call_durations = defaultdict(list)

        # Number of failed calls per tool
        self.tool_error_counts = defaultdict(int)

        # Number of validation failures per tool
        self.validation_failure_counts = defaultdict(int)

        # Number of permission denials per tool
        self.permission_denial_counts = defaultdict(int)

        # Concurrency samples over time
        self.concurrency_samples = []

    def record_tool_call(self, tool_name: str, duration_ms: float, success: bool):
        """
        Records the outcome of a tool call.
        Called in the finally block of every tool execution
        to ensure it runs regardless of success or failure.
        """
        self.tool_call_counts[tool_name] += 1
        self.tool_call_durations[tool_name].append(duration_ms)
        if not success:
            self.tool_error_counts[tool_name] += 1

    def record_validation_failure(self, tool_name: str):
        """
        Records a validation failure for a tool.
        A rising validation failure rate may indicate a Schema mismatch
        between what the model sends and what the tool expects.
        """
        self.validation_failure_counts[tool_name] += 1

    def record_permission_denial(self, tool_name: str):
        """
        Records a permission denial for a tool.
        A rising denial rate may indicate misconfigured permissions
        or an attempted unauthorized access pattern.
        """
        self.permission_denial_counts[tool_name] += 1

    def record_concurrency(self, current_count: int):
        """
        Records a concurrency sample.
        Used to track peak load and identify scaling needs.
        """
        self.concurrency_samples.append(current_count)

    def get_average_duration(self, tool_name: str) -> float:
        """
        Returns the average duration in milliseconds for a tool.
        Returns 0.0 if no calls have been recorded.
        """
        durations = self.tool_call_durations.get(tool_name, [])
        if not durations:
            return 0.0
        return sum(durations) / len(durations)

    def get_error_rate(self, tool_name: str) -> float:
        """
        Returns the error rate as a percentage for a tool.
        Returns 0.0 if no calls have been recorded.
        """
        total = self.tool_call_counts.get(tool_name, 0)
        errors = self.tool_error_counts.get(tool_name, 0)
        if total == 0:
            return 0.0
        return (errors / total) * 100

    def get_summary(self) -> dict:
        """
        Returns a summary of all recorded metrics.
        Exposed via the get_server_metrics tool and the /health endpoint.
        """
        summary = {}
        for tool_name in self.tool_call_counts:
            summary[tool_name] = {
                "total_calls": self.tool_call_counts[tool_name],
                "error_count": self.tool_error_counts[tool_name],
                "error_rate_pct": round(self.get_error_rate(tool_name), 2),
                "avg_duration_ms": round(
                    self.get_average_duration(tool_name), 2
                ),
                "validation_failures": (
                    self.validation_failure_counts[tool_name]
                ),
                "permission_denials": (
                    self.permission_denial_counts[tool_name]
                )
            }
        return summary


class AlertingSystem:
    """
    Monitors metrics and sends alerts when thresholds are exceeded.

    Thresholds are defined as class-level constants and can be
    overridden per deployment via environment variables if needed.

    In production, replace _send_alert with integrations to
    PagerDuty, Slack, or your organization's alerting platform.
    """

    # Alert thresholds
    THRESHOLDS = {
        # Alert if error rate exceeds 5%
        "error_rate_pct": 5.0,

        # Alert if average response time exceeds 2 seconds
        "avg_duration_ms": 2000.0,

        # Alert if concurrency utilization exceeds 80%
        "concurrency_utilization": 80.0
    }

    def check_and_alert(self, tool_name: str):
