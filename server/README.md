# MCP Server

Basic MCP server exposing Resources and Tools.

## Requirements

- Python 3.11+

## Installation

cd server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

## Running

python server.py

## Testing with MCP Inspector

npx @modelcontextprotocol/inspector python server.py

## Capabilities

### Resources
- document://1 — Returns a sample document

### Tools
- search_documents — Searches documents by query
  - query (string, required, max 200 chars)
  - max_results (integer, optional, 1-20, default 10)
