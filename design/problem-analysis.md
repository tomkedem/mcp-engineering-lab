# Problem Analysis

## Capabilities the System Will Need

### Read Capabilities (Resources)
- Read documents and files
- Query data from the database
- Fetch status of processes and records

### Action Capabilities (Tools)
- Update records
- Send notifications
- Trigger background processes
- Delete or archive data

### Assistance Templates (Prompts)
- Guided workflows for complex operations
- Structured interactions that require user confirmation

## Key Design Boundaries

- Read operations must never trigger side effects
- Every action must be validated against a Schema before execution
- Operational context must be explicit — never assumed
- Actions with destructive potential require confirmation before execution
- Every action must be traceable to a request, a user, and a permission
