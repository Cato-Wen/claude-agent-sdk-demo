"""
Example 16: Message Tracking
============================
Track and save all messages from query() to JSON for LLM behavior analysis.

Two usage patterns:
1. Manual tracking with MessageTracker class
2. Automatic tracking with tracked_query() wrapper
"""

import asyncio
import sys
sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT
from utils.message_tracker import MessageTracker, tracked_query


async def manual_tracking_example():
    """Example 1: Manual tracking with MessageTracker class."""
    print("\n" + "=" * 50)
    print("Manual Tracking Example")
    print("=" * 50)

    options = ClaudeAgentOptions(
        allowed_tools=["Glob", "Read"],
        cwd=str(PROJECT_ROOT),
    )

    # Create tracker with custom name
    tracker = MessageTracker(name="manual_example")

    async for message in query(
        prompt="List the Python files in the examples directory and briefly describe what example 01 does.",
        options=options
    ):
        # Track every message
        tracker.track(message)

        # Normal message handling
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")

    # Save and print summary
    tracker.print_summary()
    filepath = tracker.save()
    print(f"Analyze the JSON at: {filepath}")


async def auto_tracking_example():
    """Example 2: Automatic tracking with tracked_query() wrapper."""
    print("\n" + "=" * 50)
    print("Auto Tracking Example")
    print("=" * 50)

    options = ClaudeAgentOptions(
        allowed_tools=["Glob"],
        cwd=str(PROJECT_ROOT),
    )

    # tracked_query automatically saves when done
    async for message in tracked_query(
        prompt="What Python files exist in this project's root directory?",
        options=options,
        tracker_name="auto_example"
    ):
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")


async def main():
    """Run both tracking examples."""
    check_api_key()

    # Run manual tracking
    await manual_tracking_example()

    # Run auto tracking
    await auto_tracking_example()

    print("\n" + "=" * 50)
    print("Check the 'logs' directory for saved JSON files!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
