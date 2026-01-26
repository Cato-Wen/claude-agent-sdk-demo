"""
Example 01: Basic Query
=======================
The simplest way to use Claude Agent SDK - send a prompt and get a response.
"""

import asyncio
import sys
sys.path.append("..")

from claude_agent_sdk import query
from utils.config import check_api_key


async def main():
    """Basic query example - ask Claude a simple question."""
    check_api_key()

    print("Sending query to Claude...")
    print("-" * 40)

    async for message in query(prompt="What is the Claude Agent SDK? Explain briefly."):
        # Messages are streamed as they arrive
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")
        elif hasattr(message, "content"):
            # Handle streaming content
            content = message.content
            if isinstance(content, str):
                print(content, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
