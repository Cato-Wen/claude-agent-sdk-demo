"""
Example 06: Session Resumption
==============================
Capture session ID and resume conversations later.
"""

import asyncio
import sys
sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT
from utils.message_handler import extract_session_id


async def main():
    """Demonstrate session capture and resumption."""
    check_api_key()

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob"],
        cwd=str(PROJECT_ROOT),
    )

    print("=== First Query: Capture Session ID ===")
    print("-" * 40)

    session_id = None

    # First query - capture the session ID
    async for message in query(
        prompt="List all Python files in this project",
        options=options
    ):
        # Try to extract session ID from init message
        sid = extract_session_id(message)
        if sid:
            session_id = sid
            print(f"Captured session ID: {session_id}")

        if hasattr(message, "result"):
            print(f"\nFirst query result:\n{message.result[:300]}...")

    if not session_id:
        print("Warning: Could not capture session ID")
        return

    print("\n" + "=" * 40)
    print("=== Second Query: Resume Session ===")
    print("-" * 40)

    # Resume the session - Claude remembers the previous context
    resume_options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob"],
        cwd=str(PROJECT_ROOT),
        resume=session_id,  # Resume from previous session
    )

    async for message in query(
        prompt="Based on the files you just listed, which one is the simplest example?",
        options=resume_options
    ):
        if hasattr(message, "result"):
            print(f"\nResumed query result:\n{message.result}")


if __name__ == "__main__":
    asyncio.run(main())
