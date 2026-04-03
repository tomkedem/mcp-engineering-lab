# Capabilities

## Resource: read_document

**URI:** document/{document_id}  
**Description:** Returns the full content of a document by ID.  
**Returns:** Document title, content, metadata, and last updated timestamp.  
**Side effects:** None.  
**Error if:** Document does not exist.

---

## Tool: search_documents

**Description:** Searches documents by a text query.  
**Input:**
- query (string, max 200 chars, required)
- max_results (integer, 1-20, default 10)

**Returns:** List of matching documents with ID, title, and relevance score.  
**Side effects:** None.  
**Idempotent:** Yes.  
**Error if:** Query is empty or exceeds max length.

---

## Prompt: help_user

**Description:** Guides the model to help a user find 
relevant documents based on their need.  
**Parameters:**
- user_need (string, required): What the user is looking for.
- context (string, optional): Any additional context.

**Template:** Given the user need "{user_need}" and the 
following context "{context}", help the user find the most 
relevant documents. Ask clarifying questions if needed 
before searching.
