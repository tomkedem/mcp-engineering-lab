markdown# Production Readiness Checklist

## Code

- [ ] All Tools define complete Schema with types, ranges, and descriptions
- [ ] All Tools validate input before any business logic
- [ ] All Tools return clear errors with isError=True for invalid input
- [ ] All Resources wrap content to defend against Prompt Injection
- [ ] Destructive Tools are restricted or require approval

## Security

- [ ] All Tool calls pass through check_permission
- [ ] All data queries apply get_tenant_filter
- [ ] Logs contain no sensitive data
- [ ] .gitignore covers all secret files
- [ ] APPROVED_SERVER_HASHES defined for all external servers

## Observability

- [ ] All requests logged with Correlation ID
- [ ] Metrics configured and running
- [ ] Replay Store recording correctly
- [ ] /health endpoint returns useful information
- [ ] CI Pipeline runs all tests before every deployment

## Infrastructure

- [ ] config.validate_production() called at startup
- [ ] All required environment variables defined
- [ ] Transport set to Streamable HTTP
- [ ] Session management policy defined for Load Balancer
- [ ] Server Card configured and up to date

## Documentation

- [ ] server/README.md contains complete setup instructions
- [ ] GOVERNANCE.md defines ownership and usage policy
- [ ] All Tools and Resources documented in code
- [ ] design/architecture-patterns.md up to date
- [ ] design/capabilities.md up to date
