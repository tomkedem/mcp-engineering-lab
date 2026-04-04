import datetime
import uuid

from server.logging import safe_logger
from server.security import sanitize_for_audit


class ApprovalGate:
    """
    Manages approval requests for sensitive or high-impact operations.

    Some tool calls are too risky to execute automatically regardless
    of how confident the model is. The Approval Gate pauses execution
    and waits for explicit human confirmation before proceeding.

    When to use an Approval Gate:
    - Operations that are irreversible (bulk delete, mass notification)
    - Operations that affect a large number of records
    - Operations outside normal working hours or usage patterns
    - Operations that exceed a defined risk threshold

    How it works:
    1. Tool execution checks if approval is required
    2. If required and no approval token is present, a request is created
    3. The model receives a pending status with a request ID
    4. An approver is notified (Slack, email, etc.)
    5. The model retries the call with the approval token once approved

    In production, replace _notify_approver with your organization's
    communication tools such as Slack, PagerDuty, or email.

    Note: Approval tokens are stored in memory. In production, use a
    persistent store to survive server restarts.
    """

    def __init__(self):
        # Maps request_id to approval request details and status.
        # Replace with persistent storage in production.
        self.pending_approvals = {}

    def request_approval(
        self,
        tool_name: str,
        arguments: dict,
        user_id: str,
        reason: str
    ) -> str:
        """
        Creates a new approval request and notifies the approver.

        Arguments are sanitized before storage to prevent sensitive
        data from accumulating in the approval store.

        Returns the request ID that the model should include in the
        retry call once the operation has been approved.
        """
        request_id = str(uuid.uuid4())

        self.pending_approvals[request_id] = {
            "tool_name": tool_name,

            # Sanitized to remove sensitive fields before storage
            "arguments": sanitize_for_audit(arguments),

            "requested_by": user_id,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.datetime.utcnow().isoformat(),
            "approved_at": None,
            "rejected_at": None,
            "rejection_reason": None
        }

        # Notify the approver via the configured channel
        self._notify_approver(request_id, tool_name, user_id, reason)

        return request_id

    def approve(self, request_id: str):
        """
        Marks an approval request as approved.
        Called by the approver via the approval interface.
        """
        request = self.pending_approvals.get(request_id)
        if not request:
            raise ValueError(f"Approval request not found: {request_id}")

        request["status"] = "approved"
        request["approved_at"] = datetime.datetime.utcnow().isoformat()

        safe_logger.info(
            "Approval request approved",
            extra={"request_id": request_id, "tool": request["tool_name"]}
        )

    def reject(self, request_id: str, reason: str = "No reason provided"):
        """
        Marks an approval request as rejected.
        Called by the approver via the approval interface.
        """
        request = self.pending_approvals.get(request_id)
        if not request:
            raise ValueError(f"Approval request not found: {request_id}")

        request["status"] = "rejected"
        request["rejected_at"] = datetime.datetime.utcnow().isoformat()
        request["rejection_reason"] = reason

        safe_logger.info(
            "Approval request rejected",
            extra={
                "request_id": request_id,
                "tool": request["tool_name"],
                "reason": reason
            }
        )

    def check_approval(self, request_id: str) -> tuple[bool, str]:
        """
        Checks the current status of an approval request.

        Returns a tuple of (approved, reason):
        - (True, "Approved") if the request has been approved
        - (False, "Pending approval") if still waiting
        - (False, "Rejected: <reason>") if rejected
        - (False, "Approval request not found") if the ID is invalid
        """
        request = self.pending_approvals.get(request_id)

        if not request:
            return False, "Approval request not found"

        if request["status"] == "approved":
            return True, "Approved"

        if request["status"] == "rejected":
            return (
                False,
                f"Rejected: {request.get('rejection_reason', 'No reason provided')}"
            )

        # Still pending
        return False, "Pending approval"

    def _notify_approver(
        self,
        request_id: str,
        tool_name: str,
        user_id: str,
        reason: str
    ):
        """
        Sends a notification to the approver.

        Currently logs to the warning channel.
        In production, replace this with your organization's
        communication tool: Slack, PagerDuty, email, etc.

        The notification must include the request_id so the approver
        can reference it when approving or rejecting.
        """
        safe_logger.warning(
            "Approval required for sensitive operation",
            extra={
                "request_id": request_id,
                "tool_name": tool_name,
                "requested_by": user_id,
                "reason": reason,
                "approve_at": f"/approvals/{request_id}/approve",
                "reject_at": f"/approvals/{request_id}/reject"
            }
        )


# Singleton instance used throughout the application
approval_gate = ApprovalGate()
