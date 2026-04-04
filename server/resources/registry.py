from mcp.types import Resource

from server.resources.documents import (
    DOCUMENT_RESOURCE,
    read_document
)


# Registry of all available resources.
# Maps URI prefixes to their Resource definition and read function.
# Add new resources here after creating their module.
RESOURCE_REGISTRY: list[dict] = [
    {
        "definition": DOCUMENT_RESOURCE,

        # URI prefix used to match incoming read requests.
        # A request for "document://1" matches the prefix "document://"
        "uri_prefix": "document://",

        "handler": read_document
    }
]


def get_all_resource_definitions() -> list[Resource]:
    """
    Returns all resource definitions from the registry.
    Called by the list_resources handler in server.py.
    """
    return [entry["definition"] for entry in RESOURCE_REGISTRY]


async def read_resource(uri: str) -> list:
    """
    Routes a resource read request to the appropriate handler.
    Called by the read_resource handler in server.py.

    Matches the URI against registered prefixes and delegates to
    the corresponding handler.

    Raises ValueError if no handler is found for the given URI.
    This error is caught by the read_resource handler and returned
    to the model as a protocol-level error.
    """
    for entry in RESOURCE_REGISTRY:
        if uri.startswith(entry["uri_prefix"]):
            return await entry["handler"](uri)

    raise ValueError(
        f"Resource not found: {uri}. "
        f"Available prefixes: "
        f"{[e['uri_prefix'] for e in RESOURCE_REGISTRY]}"
    )
