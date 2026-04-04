# MCP Engineering Lab - Server

MCP server for the book "MCP Systems Engineering" by Tomer Kedem.
Built with Python and the MCP SDK. Supports both STDIO (development)
and Streamable HTTP (production) transports.

---

## Requirements

- Python 3.11+
- Node.js 18+ (for MCP Inspector only)

---

## Installation
```bash
cd server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Running

### Development (STDIO)
```bash
python server.py
```

### Production (Streamable HTTP)
```bash
export ENVIRONMENT=production
export PORT=8080
export DATABASE_PASSWORD=your_password
export API_KEY=your_api_key
export REDIS_URL=your_redis_url
python server_http.py
```

---

## Testing with MCP Inspector
```bash
npx @modelcontextprotocol/inspector python server.py
```

Open the URL printed in the terminal to inspect tools and resources.

---

## Running Tests
```bash
pytest tests/ -v
```

Run a specific test file:
```bash
pytest tests/test_contracts.py -v
pytest tests/test_security.py -v
pytest tests/test_integration.py -v
pytest tests/test_replay.py -v
```

---

## Health Check
```bash
curl http://localhost:8080/health
```

---

## Capabilities

### Resources

| URI | Description |
|-----|-------------|
| `document://1` | Returns sample document 1 |
| `document://2` | Returns sample document 2 |

### Tools

| Tool | Description | Version |
|------|-------------|---------|
| `search_documents` | Search documents by query | v2 (current) |
| `search_documents_v1` | Search documents by query | v1 (deprecated, removed 2026-06-01) |
| `get_server_metrics` | Returns server metrics summary | current |

---

## Project Structure
```
server/
├── config.py          environment configuration
├── logging.py         SafeLogger with automatic field redaction
├── metrics.py         MCPMetrics and AlertingSystem
├── replay.py          ReplayStore for failure reproduction
├── approval.py        ApprovalGate for human-in-the-loop operations
├── concurrency.py     ConcurrencyLimiter for resource protection
├── security.py        permissions, tenant isolation, capability scanning
├── utils.py           shared utilities
├── server.py          MCP server instance and STDIO entry point
├── server_http.py     HTTP entry point for production
├── discovery.py       Server Card handler
├── tools/             tool definitions and execution logic
├── resources/         resource definitions and read logic
├── tests/             automated tests
└── scripts/           CI and monitoring scripts
```

---

## Environment Variables

| Variable | Required in Production | Default | Description |
|----------|----------------------|---------|-------------|
| `ENVIRONMENT` | No | `development` | Runtime environment |
| `PORT` | No | `8080` | HTTP server port |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `DATABASE_TIMEOUT_SECONDS` | No | `5.0` | Database query timeout |
| `MAX_REQUESTS_PER_MINUTE` | No | `100` | Rate limit per user |
| `DATABASE_PASSWORD` | Yes | — | Database credentials |
| `API_KEY` | Yes | — | External API key |
| `REDIS_URL` | Yes | — | Redis connection URL for session state |

---

## Adding a New Tool

1. Create `server/tools/your_tool.py`
2. Define the `Tool` object and execution function
3. Register both in `server/tools/registry.py`
4. Add contract tests in `tests/test_contracts.py`

## Adding a New Resource

1. Create `server/resources/your_resource.py`
2. Define the `Resource` object and read function
3. Register both in `server/resources/registry.py`
