class TestSyntheticFailureScenarios:
    """
    Tests system behavior under failure conditions.
    """

    @pytest.fixture
    def user_context(self):
        return {
            "_user_id": "test_user",
            "_tenant_id": "tenant_123",
            "_correlation_id": "synthetic-test-001"
        }

    def test_tool_handles_database_timeout(self, user_context, monkeypatch):
        """
        Simulates database timeout and verifies the tool
        returns a clear error instead of hanging.
        """
        import asyncio

        async def slow_query(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate timeout

        monkeypatch.setattr("server.database.find", slow_query)

        result, is_error = asyncio.run(call_tool(
            "search_documents",
            {**user_context, "query": "test"}
        ))

        assert is_error is True
        assert "timeout" in result.text.lower() or "unavailable" in result.text.lower()

    def test_tool_handles_malformed_model_input(self, user_context):
        """
        Simulates a model sending unexpected input types.
        Verifies validation catches type mismatches.
        """
        result, is_error = asyncio.run(call_tool(
            "search_documents",
            {**user_context, "query": 12345, "max_results": "ten"}
        ))

        assert is_error is True
        assert "string" in result.text.lower() or "type" in result.text.lower()

    def test_tool_handles_concurrent_calls(self, user_context):
        """
        Simulates multiple concurrent calls to verify
        the tool handles concurrency correctly.
        """
        async def run_concurrent():
            tasks = [
                call_tool("search_documents", {**user_context, "query": f"query_{i}"})
                for i in range(10)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results

        results = asyncio.run(run_concurrent())
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Concurrent calls produced {len(errors)} errors"
