"""
Code Analyzer Project
=====================
A practical example: Build a code analysis agent that can:
- Find code smells
- Identify TODO comments
- Generate code summaries
"""

import asyncio
import sys
sys.path.append("../..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key


async def analyze_codebase(directory: str) -> dict:
    """Analyze a codebase and return findings."""
    check_api_key()

    options = ClaudeAgentOptions(
        allowed_tools=["Glob", "Grep", "Read"],
        cwd=directory,
        system_prompt="""You are a code analysis expert. When analyzing code:
1. Look for common issues (unused imports, complex functions, missing docstrings)
2. Find all TODO/FIXME comments
3. Identify potential improvements
4. Be concise and actionable in your feedback
""",
    )

    prompt = f"""
    Please analyze the Python codebase in {directory}:

    1. Find all Python files
    2. Search for TODO and FIXME comments
    3. Read a few key files and identify:
       - Missing docstrings
       - Long functions (>50 lines)
       - Complex logic that could be simplified

    Format your findings as:
    ## Summary
    - Total files analyzed
    - Key observations

    ## Issues Found
    - List each issue with file:line reference

    ## Recommendations
    - Actionable improvements
    """

    results = {
        "status": "success",
        "findings": None,
        "error": None
    }

    try:
        async for message in query(prompt=prompt, options=options):
            if hasattr(message, "result"):
                results["findings"] = message.result
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)

    return results


async def main():
    """Run the code analyzer on the examples directory."""
    import os

    # Analyze the parent examples directory
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    print("=" * 60)
    print("CODE ANALYZER")
    print("=" * 60)
    print(f"\nAnalyzing: {target_dir}")
    print("-" * 60)

    results = await analyze_codebase(target_dir)

    if results["status"] == "success":
        print("\n" + results["findings"])
    else:
        print(f"\nError: {results['error']}")


if __name__ == "__main__":
    asyncio.run(main())
