"""
Example 02: File Operations
===========================
Use Claude to read, write, and edit files.
Available tools: Read, Write, Edit
"""

import asyncio
import sys
sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT


async def main():
    """Demonstrate file operation tools."""
    check_api_key()

    # Configure allowed tools
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Edit"],
        permission_mode="acceptEdits",  # Auto-approve file changes
        cwd=str(PROJECT_ROOT),
    )

    # Task: Create and modify a file
    prompt = """
    Please do the following:
    1. Create a file called 'test_output.txt' with content "Hello from Claude Agent SDK!"
    2. Read the file back to confirm it was created
    3. Edit the file to add a second line: "This demonstrates file operations."
    4. Read the final content
    """

    print("Executing file operations...")
    print("-" * 40)

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")


if __name__ == "__main__":
    asyncio.run(main())
