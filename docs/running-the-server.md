# Running the Server

## What This Server Does

This server is a demonstration MCP server built to accompany the book
MCP Systems Engineering. It exposes two capabilities:

**Resources:**
- `document://1` — Returns sample document 1
- `document://2` — Returns sample document 2

**Tools:**
- `search_documents` — Searches documents by text query (v2, current)
- `search_documents_v1` — Deprecated search tool (removed 2026-06-01)
- `get_server_metrics` — Returns server call statistics

## Important: Sample Data Only

All data returned by this server is hardcoded sample data.
There is no real database connection.

The purpose of this server is not to demonstrate document management.
It is to demonstrate the engineering layers that every production MCP
server needs: validation, permissions, tenant isolation, logging,
metrics, replay, approval gates, contract tests, and production transport.

Take the structure. Replace the data with your own domain.

---

## Running Locally (Development)

### Prerequisites

- Python 3.11+
- Node.js 18+ (for MCP Inspector only)

### Installation
```bash
cd server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Start the Server
```bash
python server.py
```

### Inspect with MCP Inspector
```bash
npx @modelcontextprotocol/inspector python server.py
```

Open the URL printed in the terminal. You can:
- Browse the list of tools and resources
- Read `document://1` and `document://2`
- Search documents with `search_documents`
- View call statistics with `get_server_metrics`

---

## Running in Production (HTTP Transport)

### Prerequisites

Set the following environment variables before starting:
```bash
export ENVIRONMENT=production
export PORT=8080
export DATABASE_PASSWORD=your_password
export API_KEY=your_api_key
export REDIS_URL=your_redis_url
```

### Start the Server
```bash
python server_http.py
```

### Health Check
```bash
curl http://localhost:8080/health
```

### Server Card (Discovery)
```bash
curl http://localhost:8080/.well-known/mcp-server-card.json
```

---

## Running Tests
```bash
pytest tests/ -v
```

All tests should pass with sample data. No external services required.

---

## What Is Not Implemented

The following are intentionally left as integration points for you
to connect to your own infrastructure:

| Feature | Current State | What to Replace With |
|---------|--------------|---------------------|
| Document store | Hardcoded sample data | Your database |
| User authentication | Accepts any `_user_id` | Your auth system |
| Session state | In-memory dictionary | Redis or similar |
| Approval notifications | Logs to stderr | Slack, email, PagerDuty |
| External API calls | Not implemented | Your external services |

---

## Adapting This Server to Your Domain

1. Replace `server/resources/documents.py` with your own resources
2. Replace `server/tools/search.py` with your own tools
3. Register them in `server/resources/registry.py` and `server/tools/registry.py`
4. Update `server/discovery.py` with your server's capabilities
5. Update `GOVERNANCE.md` with your team's ownership and policies
6. Update `README.md` with your server's description

The security, observability, and production layers require no changes.
They are designed to work with any domain.
