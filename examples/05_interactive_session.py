"""
Example 05: Interactive Session
===============================
Use ClaudeSDKClient for multi-turn conversations.
"""

import asyncio
import sys
sys.path.append("..")

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT


async def main():
    """Demonstrate interactive session with multiple turns."""
    check_api_key()

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep"],
        cwd=str(PROJECT_ROOT),
    )

    print("Starting interactive session...")
    print("-" * 40)

    async with ClaudeSDKClient(options=options) as client:
        # First turn: Ask about the project
        print("\n[Turn 1] Asking about Python files...")
        await client.query("List all Python files in the examples directory")

        async for msg in client.receive_response():
            if hasattr(msg, "result"):
                print(f"Response: {msg.result[:200]}...")

        # Second turn: Follow-up question (maintains context)
        print("\n[Turn 2] Follow-up question...")
        await client.query("How many files did you find? Which one handles file operations?")

        async for msg in client.receive_response():
            if hasattr(msg, "result"):
                print(f"Response: {msg.result}")


if __name__ == "__main__":
    asyncio.run(main())
