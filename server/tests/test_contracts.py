import pytest
import asyncio
import json
from server import call_tool, list_tools

class TestSearchDocumentsContract:
    """
    Contract tests for search_documents tool.
    Tests that the tool honors its Schema under all conditions.
    """

    @pytest.fixture
    def valid_arguments(self):
        return {
            "query": "sample query",
            "max_results": 5,
            "_user_id": "test_user",
            "_tenant_id": "test_tenant",
            "_correlation_id": "test-correlation-id"
        }

    def test_tool_is_registered(self):
        """Tool must appear in the tools list with correct schema."""
        tools = asyncio.run(list_tools())
        tool_names = [t.name for t in tools]
        assert "search_documents" in tool_names

    def test_schema_has_required_fields(self):
        """Schema must define required fields correctly."""
        tools = asyncio.run(list_tools())
        tool = next(t for t in tools if t.name == "search_documents")
        schema = tool.inputSchema

        assert "query" in schema["properties"]
        assert "query" in schema["required"]
        assert "max_results" not in schema.get("required", [])

    def test_valid_input_returns_list(self, valid_arguments):
        """Valid input must return a non-empty result in JSON format."""
        result, *rest = asyncio.run(call_tool("search_documents", valid_arguments))
        is_error = rest[0] if rest else False

        assert not is_error
        parsed = json.loads(result.text)
        assert isinstance(parsed, list)

    def test_result_items_have_required_fields(self, valid_arguments):
        """Each result item must contain id, title, and score."""
        result, *_ = asyncio.run(call_tool("search_documents", valid_arguments))
        parsed = json.loads(result.text)

        for item in parsed:
            assert "id" in item, "Result item missing 'id'"
            assert "title" in item, "Result item missing 'title'"
            assert "score" in item, "Result item missing 'score'"

    def test_score_is_between_zero_and_one(self, valid_arguments):
        """Score field must be a float between 0 and 1."""
        result, *_ = asyncio.run(call_tool("search_documents", valid_arguments))
        parsed = json.loads(result.text)

        for item in parsed:
            assert 0.0 <= item["score"] <= 1.0, f"Invalid score: {item['score']}"

    def test_max_results_is_respected(self, valid_arguments):
        """Result count must not exceed max_results."""
        valid_arguments["max_results"] = 2
        result, *_ = asyncio.run(call_tool("search_documents", valid_arguments))
        parsed = json.loads(result.text)

        assert len(parsed) <= 2

    def test_empty_query_returns_error(self, valid_arguments):
        """Empty query must return isError=True with clear message."""
        valid_arguments["query"] = ""
        result, is_error = asyncio.run(call_tool("search_documents", valid_arguments))

        assert is_error is True
        assert "empty" in result.text.lower()

    def test_missing_query_returns_error(self, valid_arguments):
        """Missing required field must return isError=True."""
        del valid_arguments["query"]
        result, is_error = asyncio.run(call_tool("search_documents", valid_arguments))

        assert is_error is True
        assert "query" in result.text.lower()

    def test_max_results_above_limit_returns_error(self, valid_arguments):
        """max_results above maximum must return isError=True."""
        valid_arguments["max_results"] = 100
        result, is_error = asyncio.run(call_tool("search_documents", valid_arguments))

        assert is_error is True
        assert "20" in result.text

    def test_query_at_max_length_is_accepted(self, valid_arguments):
        """Query exactly at max length must be accepted."""
        valid_arguments["query"] = "a" * 200
        result, *rest = asyncio.run(call_tool("search_documents", valid_arguments))
        is_error = rest[0] if rest else False

        assert not is_error

    def test_query_above_max_length_returns_error(self, valid_arguments):
        """Query above max length must return isError=True."""
        valid_arguments["query"] = "a" * 201
        result, is_error = asyncio.run(call_tool("search_documents", valid_arguments))

        assert is_error is True
        assert "200" in result.text
