# Architecture Patterns

## Chosen Patterns

### Pattern 1: Read-Only Server
**Rationale:** Separates read operations from write operations.
All analysis and reporting tools use the read-only server.
No risk of accidental data modification during analysis.

**Applied to:** documents-server (read-only)
All tools in this server return data only. No tool modifies state.

### Pattern 2: Policy Enforcement Layer
**Rationale:** Centralizes organizational policies in one place.
All tool calls pass through the policy layer before execution.
Policies can be updated without touching server code.

**Policies defined:**
- Bulk operations > 100 records require approval
- Destructive actions blocked in production
- Rate limiting per user per tool

## Layer Separation

read layer:
  server: documents-server
  tools: search_documents, read_document
  policy: open to all authenticated users

action layer:
  server: actions-server
  tools: update_document, delete_document
  policy: requires explicit write permission

## Anti-Patterns Avoided

- No single server doing everything
- No policy enforcement via prompts
- No global state shared between sessions
```

העלה את הקובץ לגיטהאב. לאחר מכן ארגן מחדש את תיקיית `server/` כך שתשקף את ההפרדה בין Read Layer ל-Action Layer:
```
server/
├── read_server.py        ← read-only capabilities
├── action_server.py      ← action capabilities  
├── policy.py             ← policy enforcement layer
├── tests/
│   ├── test_contracts.py
│   ├── test_integration.py
│   ├── test_security.py
│   └── test_replay.py
└── README.md
