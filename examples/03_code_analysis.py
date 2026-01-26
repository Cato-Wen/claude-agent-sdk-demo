"""
Example 03: Code Analysis
=========================
Use Claude to search and analyze code.
Available tools: Glob, Grep, Read
"""

import asyncio
import sys
sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT


async def main():
    """Demonstrate code analysis tools."""
    check_api_key()

    options = ClaudeAgentOptions(
        allowed_tools=["Glob", "Grep", "Read"],
        cwd=str(PROJECT_ROOT),
    )

    # Task: Analyze the demo project structure
    prompt = """
    Please analyze this project:
    1. Use Glob to find all Python files (*.py)
    2. Use Grep to search for any TODO comments
    3. Read one of the example files and summarize what it does

    Give me a brief overview of the project structure.
    """

    print("Analyzing code...")
    print("-" * 40)

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")


if __name__ == "__main__":
    asyncio.run(main())
