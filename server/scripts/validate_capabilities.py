import asyncio
import json
import sys
from server import compute_capabilities_hash, APPROVED_SERVER_HASHES

async def validate_all_servers():
    """
    Validates that all external servers match their approved hashes.
    Fails the CI pipeline if any server has changed.
    """
    all_valid = True

    for server_name, approved_hash in APPROVED_SERVER_HASHES.items():
        try:
            current_tools = await fetch_server_tools(server_name)
            unchanged, reason = verify_capabilities_unchanged(
                server_name, current_tools, approved_hash
            )

            if unchanged:
                print(f"✓ {server_name}: capabilities unchanged")
            else:
                print(f"✗ {server_name}: {reason}")
                all_valid = False

        except Exception as e:
            print(f"✗ {server_name}: failed to connect - {str(e)}")
            all_valid = False

    return all_valid

if __name__ == "__main__":
    valid = asyncio.run(validate_all_servers())
    sys.exit(0 if valid else 1)
