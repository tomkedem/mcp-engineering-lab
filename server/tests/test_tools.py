import pytest
from server import validate_search_input

def test_valid_input():
    """Valid input passes validation."""
    error = validate_search_input({"query": "sample", "max_results": 5})
    assert error is None

def test_empty_query():
    """Empty query returns clear error."""
    error = validate_search_input({"query": ""})
    assert error is not None
    assert "empty" in error.lower()

def test_missing_query():
    """Missing required parameter returns clear error."""
    error = validate_search_input({})
    assert error is not None
    assert "query" in error.lower()

def test_query_too_long():
    """Query exceeding max length returns clear error."""
    error = validate_search_input({"query": "a" * 201})
    assert error is not None
    assert "200" in error

def test_invalid_max_results():
    """max_results outside valid range returns clear error."""
    error = validate_search_input({"query": "sample", "max_results": 99})
    assert error is not None
    assert "20" in error
