"""
Example 11: Skills Demo
=======================
Demonstrate how to use Claude Agent SDK's Skill capability.

Skills are specialized capabilities defined in SKILL.md files that Claude
automatically invokes when relevant to the user's request.

Skill files location:
- Project Skills: .claude/skills/<skill-name>/SKILL.md
- User Skills: ~/.claude/skills/<skill-name>/SKILL.md
"""

import asyncio
import sys
sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT


async def list_available_skills():
    """List all available skills in the project."""
    check_api_key()

    print("=" * 60)
    print("LISTING AVAILABLE SKILLS")
    print("=" * 60)

    options = ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        setting_sources=["project"],  # Load skills from .claude/skills/
        allowed_tools=["Skill"],
    )

    async for message in query(
        prompt="What skills are available? List them with their descriptions.",
        options=options
    ):
        if hasattr(message, "result"):
            print(f"\n{message.result}")
        elif hasattr(message, "content"):
            content = message.content
            if isinstance(content, str):
                print(content, end="", flush=True)


async def use_code_reviewer_skill():
    """Use the code-reviewer skill to review code."""
    check_api_key()

    print("\n" + "=" * 60)
    print("USING CODE-REVIEWER SKILL")
    print("=" * 60)

    options = ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        setting_sources=["project"],  # Required to load skills from filesystem
        allowed_tools=["Skill", "Read", "Glob", "Grep"],  # Skill + tools the skill needs
    )

    prompt = """
    Please review the Python code in the examples directory.
    Focus on:
    1. Code quality issues
    2. Any potential bugs
    3. Suggestions for improvement

    Use the code-reviewer skill for this task.
    """

    print(f"\nReviewing code in: {PROJECT_ROOT / 'examples'}")
    print("-" * 60)

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\n{message.result}")
        elif hasattr(message, "content"):
            content = message.content
            if isinstance(content, str):
                print(content, end="", flush=True)


async def invoke_skill_directly():
    """Invoke a skill directly by name."""
    check_api_key()

    print("\n" + "=" * 60)
    print("INVOKING SKILL DIRECTLY")
    print("=" * 60)

    options = ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        setting_sources=["project"],
        allowed_tools=["Skill", "Read", "Glob", "Grep"],
    )

    # You can invoke skills directly using /skill-name syntax
    prompt = """
    Run /code-reviewer on the file examples/01_basic_query.py
    """

    print("\nDirectly invoking code-reviewer skill...")
    print("-" * 60)

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\n{message.result}")
        elif hasattr(message, "content"):
            content = message.content
            if isinstance(content, str):
                print(content, end="", flush=True)


async def main():
    """Run skill demos."""
    print("\n" + "#" * 60)
    print("# CLAUDE AGENT SDK - SKILLS DEMO")
    print("#" * 60)

    # Demo 1: List available skills
    await list_available_skills()

    # Demo 2: Use the code-reviewer skill
    await use_code_reviewer_skill()

    # Uncomment to run direct invocation demo:
    # await invoke_skill_directly()


if __name__ == "__main__":
    asyncio.run(main())
