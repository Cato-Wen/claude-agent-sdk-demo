"""
Example 07: Hooks and Logging
=============================
Use hooks to monitor, log, or modify agent behavior.
"""

import asyncio
import sys
from datetime import datetime
sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT


# Define hook handlers
def on_pre_tool_use(tool_name: str, tool_input: dict) -> dict | None:
    """Called before each tool execution."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] PRE-TOOL: {tool_name}")
    print(f"  Input: {str(tool_input)[:100]}...")

    # You can modify the input or return None to block the tool
    # Example: Block dangerous commands
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        dangerous = ["rm -rf", "sudo", "format", "del /"]
        if any(d in command for d in dangerous):
            print(f"  [BLOCKED] Dangerous command detected!")
            return None  # Block execution

    return tool_input  # Allow execution


def on_post_tool_use(tool_name: str, tool_input: dict, tool_output: str):
    """Called after each tool execution."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] POST-TOOL: {tool_name}")
    print(f"  Output length: {len(tool_output)} chars")


def on_session_start():
    """Called when session starts."""
    print("\n" + "=" * 50)
    print("SESSION STARTED")
    print("=" * 50 + "\n")


def on_session_end():
    """Called when session ends."""
    print("\n" + "=" * 50)
    print("SESSION ENDED")
    print("=" * 50)


async def main():
    """Demonstrate hooks for monitoring and control."""
    check_api_key()

    # Configure hooks
    hooks = {
        "PreToolUse": on_pre_tool_use,
        "PostToolUse": on_post_tool_use,
        "SessionStart": on_session_start,
        "SessionEnd": on_session_end,
    }

    options = ClaudeAgentOptions(
        allowed_tools=["Glob", "Read", "Bash"],
        cwd=str(PROJECT_ROOT),
        hooks=hooks,
    )

    prompt = """
    Please:
    1. List Python files in the examples directory
    2. Read the first example file
    3. Show the current directory
    """

    print("Running with hooks enabled...")
    print("-" * 40)

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\nFinal Result:\n{message.result}")


if __name__ == "__main__":
    asyncio.run(main())
