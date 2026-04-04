# Governance

## Ownership

This server is owned and maintained by [team name].
For questions or issues, open a GitHub issue or contact [contact].

## Who Can Connect

Any host application that has been approved by the owning team.
To request access, open an issue with the label "access-request".

## Usage Policy

- Tools may be called up to 100 times per user per minute
- Bulk operations affecting more than 100 records require approval
- Destructive operations are blocked in production
- All tool calls are logged and audited

## Change Policy

- Non-breaking changes (new optional parameters, new fields in results)
  are deployed without prior notice
- Breaking changes require a minimum of 30 days notice
- Deprecated tools are announced in the changelog and removed
  after the stated removal date

## Versioning

This server follows semantic versioning.
The current version is available at /.well-known/mcp-server-card.json

## Security

To report a security issue, contact [security contact] directly.
Do not open a public GitHub issue for security vulnerabilities.

## SLA

This server targets 99.9% availability during business hours.
No SLA applies outside business hours unless explicitly agreed.
