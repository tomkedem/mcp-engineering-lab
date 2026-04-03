# System Overview

## Components

### Host
The environment where everything runs.
Manages user experience, permissions, and connected MCP servers.
The user's trust boundary.

### Client
The communication layer inside the Host.
Speaks to MCP servers on behalf of the Host.
Ensures the protocol is respected on both sides.

### MCP Server
The capability provider.
Exposes tools, resources, and prompt templates.
Each server is responsible for one domain only.

### Model
Receives context and returns decisions or actions.
Does not communicate directly with MCP servers.
Works through the Host which mediates on its behalf.

## Capability Types

| Type | Purpose | Changes System State? |
|------|---------|----------------------|
| Resource | Expose data for the model to read | No |
| Tool | Execute an action in the system | Yes |
| Prompt | Structured interaction template | No |

## Architecture Diagram

                    Model
                      │
                      ▼
                    Host
                      │
                    Client
                   /  |  \
                  ▼   ▼   ▼
         Server     Server     Server
        (Database) (Documents) (Notifications)
