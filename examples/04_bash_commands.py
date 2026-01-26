"""
Example 04: Bash Commands
=========================
Execute shell commands through Claude.
Available tools: Bash
"""

import asyncio
import sys
sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT


async def main():
    """Demonstrate Bash command execution."""
    check_api_key()

    options = ClaudeAgentOptions(
        allowed_tools=["Bash"],
        cwd=str(PROJECT_ROOT),
    )

    # Task: Execute some safe commands
    prompt = """
    Please execute the following commands and show me the output:
    1. Show the current directory (pwd or cd)
    2. List files in the current directory
    3. Show Python version (python --version)
    4. Show pip version (pip --version)
    """

    print("Executing bash commands...")
    print("-" * 40)

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")


if __name__ == "__main__":
    asyncio.run(main())
