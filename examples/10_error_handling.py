"""
Example 10: Error Handling
==========================
Proper error handling patterns for production use.
"""

import asyncio
import sys
sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.exceptions import (
    CLINotFoundError,
    ProcessError,
    CLIJSONDecodeError,
)
from utils.config import check_api_key, PROJECT_ROOT


async def safe_query(prompt: str, options: ClaudeAgentOptions) -> str | None:
    """Execute a query with comprehensive error handling."""
    try:
        result = None
        async for message in query(prompt=prompt, options=options):
            if hasattr(message, "result"):
                result = message.result
        return result

    except CLINotFoundError:
        print("ERROR: Claude Code CLI not found!")
        print("Install it with: pip install claude-agent-sdk")
        return None

    except ProcessError as e:
        print(f"ERROR: Process execution failed: {e}")
        return None

    except CLIJSONDecodeError as e:
        print(f"ERROR: Failed to parse response: {e}")
        return None

    except asyncio.TimeoutError:
        print("ERROR: Request timed out")
        return None

    except Exception as e:
        print(f"ERROR: Unexpected error: {type(e).__name__}: {e}")
        return None


async def main():
    """Demonstrate error handling patterns."""
    check_api_key()

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob"],
        cwd=str(PROJECT_ROOT),
        max_turns=5,  # Limit turns to prevent infinite loops
    )

    print("Testing error handling...")
    print("-" * 40)

    # Test 1: Valid query
    print("\n[Test 1] Valid query:")
    result = await safe_query(
        "List Python files in the examples directory",
        options
    )
    if result:
        print(f"Success! Result length: {len(result)} chars")

    # Test 2: Query that might fail (file doesn't exist)
    print("\n[Test 2] Query for non-existent file:")
    result = await safe_query(
        "Read the file 'nonexistent_file_xyz.py'",
        options
    )
    if result:
        print(f"Result: {result[:200]}...")
    else:
        print("Query failed or returned no result")

    # Test 3: Timeout handling (with very short timeout)
    print("\n[Test 3] Demonstrating timeout awareness:")
    timeout_options = ClaudeAgentOptions(
        allowed_tools=["Read"],
        cwd=str(PROJECT_ROOT),
        max_turns=2,  # Very limited turns
    )
    result = await safe_query(
        "Quickly read the README if it exists",
        timeout_options
    )
    if result:
        print(f"Success! Got response within limits")


if __name__ == "__main__":
    asyncio.run(main())
