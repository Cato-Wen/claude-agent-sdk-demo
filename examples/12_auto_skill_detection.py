"""
Example 12: Auto Skill Detection Demo
=====================================
Demonstrate how Claude automatically identifies and selects the appropriate skill
based on the task description.

Key insights:
- The MODEL (Claude) decides which skill to use based on task + skill descriptions
- The SDK executes the skill through the Skill tool
- We can use HOOKS to capture skill invocations and see which skill was selected

Hook Structure (per SDK types.py):
- hooks: dict[HookEvent, list[HookMatcher]]
- HookMatcher has: matcher (tool name pattern), hooks (list of async callbacks), timeout
- HookCallback signature: async (HookInput, tool_use_id, context) -> HookJSONOutput
"""

import asyncio
import sys
from datetime import datetime
from typing import Any

sys.path.append("..")
# Fix Windows console encoding for emoji/unicode output
sys.stdout.reconfigure(encoding='utf-8')

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import HookMatcher, HookInput, HookContext, SyncHookJSONOutput
from utils.config import check_api_key, PROJECT_ROOT


# Track which skills were used
skills_used: list[dict] = []


async def on_pre_tool_use(
    hook_input: HookInput,
    tool_use_id: str | None,
    context: HookContext
) -> SyncHookJSONOutput:
    """Intercept tool calls to detect skill usage (async hook callback)."""
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Extract tool info from hook_input
    tool_name = hook_input.get("tool_name", "unknown")
    tool_input = hook_input.get("tool_input", {})

    # Detect Skill tool invocation
    if tool_name == "Skill":
        skill_name = tool_input.get("skill", "unknown")
        skill_args = tool_input.get("args", "")

        print(f"\n{'='*60}")
        print(f"[{timestamp}] SKILL DETECTED!")
        print(f"  Skill Name: {skill_name}")
        if skill_args:
            print(f"  Arguments: {skill_args}")
        print(f"{'='*60}\n")

        # Record the skill usage
        skills_used.append({
            "timestamp": timestamp,
            "skill": skill_name,
            "args": skill_args
        })
    else:
        # Log other tool calls (briefly)
        print(f"[{timestamp}] Tool: {tool_name}")

    # Return empty output to allow execution
    return {}


async def on_post_tool_use(
    hook_input: HookInput,
    tool_use_id: str | None,
    context: HookContext
) -> SyncHookJSONOutput:
    """Log tool completion (async hook callback)."""
    tool_name = hook_input.get("tool_name", "unknown")
    tool_response = hook_input.get("tool_response", "")

    if tool_name == "Skill":
        response_len = len(str(tool_response)) if tool_response else 0
        print(f"  [Skill execution completed - output length: {response_len} chars]")

    return {}


async def run_task_with_skill_detection(task_description: str, task_prompt: str):
    """Run a task and detect which skill is automatically selected."""
    global skills_used
    skills_used = []  # Reset for each task

    print("\n" + "#" * 60)
    print(f"# TASK: {task_description}")
    print("#" * 60)
    print(f"\nPrompt: {task_prompt.strip()}")
    print("-" * 60)

    # Hooks use HookMatcher structure:
    # - matcher: tool name pattern (None = match all tools)
    # - hooks: list of async callback functions
    hooks = {
        "PreToolUse": [
            HookMatcher(
                matcher=None,  # Match all tools
                hooks=[on_pre_tool_use]
            )
        ],
        "PostToolUse": [
            HookMatcher(
                matcher=None,  # Match all tools
                hooks=[on_post_tool_use]
            )
        ],
    }

    options = ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        setting_sources=["project"],  # Load skills from .claude/skills/
        allowed_tools=["Skill", "Read", "Glob", "Grep"],
        hooks=hooks,
    )

    try:
        async for message in query(prompt=task_prompt, options=options):
            # Debug: show message types
            msg_type = type(message).__name__
            if hasattr(message, 'subtype'):
                print(f"  [MSG] {msg_type} (subtype: {message.subtype})")
            elif hasattr(message, 'content'):
                # Check for tool use in content
                content = message.content
                if isinstance(content, list):
                    for item in content:
                        if hasattr(item, 'name'):  # ToolUseBlock
                            print(f"  [TOOL_USE] {item.name}")
                            if item.name == "Skill":
                                skill_name = item.input.get("skill", "unknown")
                                print(f"    -> Skill invoked: {skill_name}")
                                skills_used.append({
                                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                                    "skill": skill_name,
                                    "args": item.input.get("args", "")
                                })

            if hasattr(message, "result"):
                # Print truncated result
                result = message.result
                if len(result) > 500:
                    result = result[:500] + "\n... [truncated]"
                print(f"\nResult:\n{result}")
    except Exception as e:
        print(f"Error: {e}")

    # Summary of skills used
    print("\n" + "=" * 60)
    print("SKILL USAGE SUMMARY")
    print("=" * 60)
    if skills_used:
        for i, skill in enumerate(skills_used, 1):
            print(f"  {i}. [{skill['timestamp']}] {skill['skill']}")
            if skill['args']:
                print(f"     Args: {skill['args']}")
    else:
        print("  No skills were invoked for this task.")
    print("=" * 60)

    return skills_used


async def main():
    """Demo: Auto skill detection with different task types."""
    check_api_key()

    print("\n" + "=" * 70)
    print("  CLAUDE AGENT SDK - AUTO SKILL DETECTION DEMO")
    print("  ")
    print("  This demo shows how Claude automatically selects the appropriate")
    print("  skill based on the task description.")
    print("=" * 70)

    # Test Case 1: AUTO SELECTION - No skill mentioned, just describe the task
    # The model should recognize this matches "code-reviewer" skill description
    await run_task_with_skill_detection(
        task_description="AUTO: Code Review (no skill mentioned)",
        task_prompt="""
        Review the Python code in examples/01_basic_query.py.
        Check for bugs, security issues, and code quality problems.
        """
    )

    # Test Case 2: AUTO SELECTION - Documentation task without mentioning skill
    # The model should recognize this matches "doc-generator" skill description
    await run_task_with_skill_detection(
        task_description="AUTO: Documentation (no skill mentioned)",
        task_prompt="""
        Generate API documentation with docstrings for utils/message_handler.py.
        Include usage examples.
        """
    )

    # Test Case 3: Explicit invocation for comparison
    await run_task_with_skill_detection(
        task_description="EXPLICIT: /code-reviewer syntax",
        task_prompt="""
        Run /code-reviewer on examples/02_file_operations.py
        """
    )

    # Final summary
    print("\n" + "=" * 70)
    print("  DEMO COMPLETE")
    print("  ")
    print("  Key Takeaways:")
    print("  1. Use /skill-name syntax to explicitly invoke a skill")
    print("  2. Or mention 'use the <skill-name> skill' in the prompt")
    print("  3. Hooks capture skill invocations via the Skill tool")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
