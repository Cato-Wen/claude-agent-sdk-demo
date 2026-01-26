"""
Example 08: Web Search
======================
Use Claude's web capabilities to search and fetch information.
Available tools: WebSearch, WebFetch
"""

import asyncio
import sys
sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key


async def main():
    """Demonstrate web search and fetch capabilities."""
    check_api_key()

    options = ClaudeAgentOptions(
        allowed_tools=["WebSearch", "WebFetch"],
    )

    prompt = """
    Please search for "Claude Agent SDK Python" and summarize:
    1. What is it used for?
    2. What are its main features?
    3. How to get started?

    Keep the summary concise.
    """

    print("Searching the web...")
    print("-" * 40)

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")


if __name__ == "__main__":
    asyncio.run(main())
