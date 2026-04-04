# MCP Systems Engineering
## Building AI Systems with Model Context Protocol

> Companion repository for the book **MCP Systems Engineering** by Tomer Kedem

---

## About This Project

This repository evolves chapter by chapter alongside the book.
Each chapter adds a new layer to the system — a working component,
a design decision, a security layer, or a structure built to last.

The goal is not just to accumulate knowledge, but to build a real system.

---

## Repository Structure

| Folder | Contents |
|--------|----------|
| `docs/` | Documentation and explanations per chapter |
| `design/` | Architecture and design documents |
| `server/` | The MCP server, evolving throughout the book |
| `samples/` | Code samples organized by chapter |
| `tests/` | Automated tests |

---

## Prerequisites

- Python 3.11+
- Node.js 18+ (for MCP Inspector only)
- A GitHub account

---

## How to Use This Repository

Each chapter in the book references the relevant files for that stage.
Read the chapter first, then open the corresponding code.
The server evolves gradually — do not skip ahead.

---

## Quick Start
```bash
cd server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

---

## Book Chapters and Repository Progress

| Chapter | Topic | Files Added |
|---------|-------|-------------|
| Intro | Project setup | `README.md`, `docs/intro.md` |
| 1 | Why MCP | `docs/why-mcp.md` |
| 2 | Problem analysis | `design/problem-analysis.md` |
| 3 | System overview | `design/system-overview.md` |
| 4 | Architecture | `design/structure.md` |
| 5 | Capabilities | `design/capabilities.md` |
| 6 | First server | `server/server.py` |
| 7 | Tool design | `server/tools/` |
| 8 | Context and state | `design/` workflows |
| 9 | Security | `server/security.py` |
| 10 | Observability | `server/logging.py`, `server/metrics.py` |
| 11 | Architecture patterns | `design/architecture-patterns.md` |
| 12 | Production | `server/server_http.py`, `GOVERNANCE.md` |

---

## License

MIT License — free to use, learn from, and extend.

---

## Version

This repository accompanies **MCP Systems Engineering** by Tomer Kedem.
Final version as of book publication.

For updates and community discussions:
github.com/tomerkedem/mcp-engineering-lab
