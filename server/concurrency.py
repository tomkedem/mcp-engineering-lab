import asyncio

from server.logging import safe_logger


class ConcurrencyLimiter:
    """
    Limits the number of concurrent tool executions on the server.

    Without a concurrency limit, a burst of simultaneous requests can
    exhaust server resources: memory, database connections, and external
    API rate limits. The limiter acts as a controlled gate that allows
    a defined number of executions to proceed simultaneously while
    queuing the rest.

    How it works:
    - Uses asyncio.Semaphore to limit concurrent access
    - Callers await acquire() before execution
    - Callers call release() in a finally block after execution
    - If the limit is reached, acquire() waits until a slot is free

    Choosing max_concurrent:
    - Too low: requests queue up and response times increase
    - Too high: server resources are exhausted under peak load
    - Start with 50 and adjust based on observed Metrics

    In production, monitor concurrency utilization via get_summary()
    and alert when it consistently exceeds 80%.

    Usage:
        await limiter.acquire()
        try:
            result = await execute_tool(...)
        finally:
            limiter.release()
    """

    def __init__(self, max_concurrent: int = 50):
        """
        Initializes the limiter with a maximum concurrency level.

        Args:
            max_concurrent: Maximum number of simultaneous tool executions.
                            Default is 50. Adjust based on server capacity.
        """
        # asyncio.Semaphore enforces the concurrency limit
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Tracks the current number of active executions
        self.current_count = 0

        # Maximum allowed concurrent executions
        self.max_concurrent = max_concurrent

    async def acquire(self):
        """
        Acquires a slot for execution.

        Waits asynchronously if the maximum concurrency level has been
        reached. Does not block the event loop while waiting.
        """
        await self.semaphore.acquire()
        self.current_count += 1

        safe_logger.info(
            "Concurrency slot acquired",
            extra={
                "current": self.current_count,
                "max": self.max_concurrent,
                "utilization_pct": round(self.utilization, 1)
            }
        )

    def release(self):
        """
        Releases a slot after execution completes.

        Must be called in a finally block to ensure the slot is always
        released, even if the execution raises an exception.
        """
        self.current_count -= 1
        self.semaphore.release()

    @property
    def utilization(self) -> float:
        """
        Returns current utilization as a percentage.

        A sustained utilization above 80% is a signal to either
        increase max_concurrent or add more server instances.
        """
        return (self.current_count / self.max_concurrent) * 100

    def get_summary(self) -> dict:
        """
        Returns a snapshot of current concurrency state.

        Included in the server metrics summary for monitoring.
        """
        return {
            "current_concurrent": self.current_count,
            "max_concurrent": self.max_concurrent,
            "utilization_pct": round(self.utilization, 1),
            "available_slots": self.max_concurrent - self.current_count
        }


# Singleton instance used throughout the application.
# max_concurrent can be tuned based on server capacity and observed load.
limiter = ConcurrencyLimiter(max_concurrent=50)
