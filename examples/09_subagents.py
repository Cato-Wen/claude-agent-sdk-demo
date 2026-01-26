"""
Example 09: Subagents
=====================
Spawn specialized subagents for focused tasks.
Uses the Task tool to delegate work.
"""

import asyncio
import sys
sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT


async def main():
    """Demonstrate subagent delegation."""
    check_api_key()

    # Define specialized subagents
    agents = {
        "code-analyzer": {
            "description": "Analyzes Python code for patterns and issues",
            "tools": ["Read", "Glob", "Grep"],
            "system_prompt": "You are a code analysis expert. Focus on code quality and patterns."
        },
        "file-manager": {
            "description": "Handles file operations",
            "tools": ["Read", "Write", "Edit"],
            "system_prompt": "You are a file management specialist."
        }
    }

    options = ClaudeAgentOptions(
        allowed_tools=["Task", "Read", "Glob"],  # Task tool enables subagents
        cwd=str(PROJECT_ROOT),
        agents=agents,
    )

    prompt = """
    I need help analyzing this project. Please:

    1. Use the code-analyzer subagent to find all function definitions in the examples directory
    2. Summarize what each example demonstrates

    Delegate the detailed analysis work to the appropriate subagent.
    """

    print("Running with subagents...")
    print("-" * 40)

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")


if __name__ == "__main__":
    asyncio.run(main())
