# Project Structure

## Components

### Host
The application that runs the model and manages user interaction.
Responsible for permissions, context preparation, and user trust.

### Client
Built into the Host using the MCP SDK.
Handles all communication with MCP Servers.

### MCP Server
Located in the /server directory.
Exposes capabilities to the model through the MCP protocol.
Each server is responsible for one domain only.

## Capability Plan

| Capability | Type | Server | Description |
|------------|------|--------|-------------|
| read_document | Resource | documents-server | Read a document by ID |
| search_documents | Tool | documents-server | Search documents by query |
| send_notification | Tool | notifications-server | Send a notification to a user |
| summarize_template | Prompt | documents-server | Summarize a document |

## State Management Decision

Session state is held in the Host.
No persistent state between sessions at this stage.
Will revisit when long-running workflows are introduced.
```


