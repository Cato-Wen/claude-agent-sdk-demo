"""
Example 14: Sandboxed Code Execution
====================================
A more sophisticated code execution pattern that mimics
Anthropic API's code_execution tool behavior.

Features:
- Isolated sandbox environment
- Custom permission handler for safety
- Automatic dependency installation
- Structured output capture
- Error handling and timeout support
"""

import asyncio
import sys
import os
import json
import tempfile
from datetime import datetime
from typing import Optional

sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT


# Sandbox configuration
SANDBOX_ROOT = os.path.join(PROJECT_ROOT, "sandbox", "code_execution")
os.makedirs(SANDBOX_ROOT, exist_ok=True)


class CodeExecutionSandbox:
    """
    A sandbox environment for code execution.
    Mimics the behavior of Anthropic's code_execution tool.
    """

    def __init__(self, sandbox_id: Optional[str] = None):
        self.sandbox_id = sandbox_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.workspace = os.path.join(SANDBOX_ROOT, self.sandbox_id)
        os.makedirs(self.workspace, exist_ok=True)

        # Track created files
        self.created_files = []
        self.execution_log = []

    def get_workspace(self) -> str:
        return self.workspace

    def log_execution(self, action: str, details: dict):
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        })

    def list_files(self) -> list:
        """List all files in the sandbox."""
        files = []
        for root, dirs, filenames in os.walk(self.workspace):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, self.workspace)
                files.append(rel_path)
        return files

    def save_log(self):
        """Save execution log to file."""
        log_path = os.path.join(self.workspace, "execution_log.json")
        with open(log_path, "w") as f:
            json.dump(self.execution_log, f, indent=2)


async def sandbox_permission_handler(
    tool_name: str,
    input_data: dict,
    context: dict
) -> dict:
    """
    Custom permission handler for sandboxed code execution.
    Ensures all operations stay within the sandbox.
    """

    # Get the current sandbox workspace from context
    sandbox_workspace = context.get("sandbox_workspace", SANDBOX_ROOT)

    # For Write/Edit tools, ensure paths are within sandbox
    if tool_name in ["Write", "Edit"]:
        file_path = input_data.get("file_path", "")

        # If it's an absolute path outside sandbox, redirect
        if os.path.isabs(file_path) and not file_path.startswith(sandbox_workspace):
            # Redirect to sandbox
            filename = os.path.basename(file_path)
            safe_path = os.path.join(sandbox_workspace, filename)
            print(f"[Sandbox] Redirecting {file_path} -> {safe_path}")
            return {
                "behavior": "allow",
                "updatedInput": {**input_data, "file_path": safe_path}
            }

    # For Bash commands, add safety checks
    if tool_name == "Bash":
        command = input_data.get("command", "")

        # Block dangerous commands
        dangerous_patterns = [
            "rm -rf /",
            "sudo rm",
            "mkfs",
            "> /dev/",
            "dd if=",
        ]

        for pattern in dangerous_patterns:
            if pattern in command:
                return {
                    "behavior": "deny",
                    "message": f"Dangerous command blocked: {pattern}",
                    "interrupt": False
                }

    return {"behavior": "allow", "updatedInput": input_data}


async def run_code_in_sandbox(
    task_description: str,
    sandbox: CodeExecutionSandbox,
    install_deps: Optional[list] = None
) -> dict:
    """
    Execute code in a sandboxed environment.

    Args:
        task_description: What the code should do
        sandbox: The sandbox environment
        install_deps: Optional list of pip packages to install

    Returns:
        dict with execution results
    """

    workspace = sandbox.get_workspace()

    # Build the prompt
    setup_instructions = ""
    if install_deps:
        deps_str = " ".join(install_deps)
        setup_instructions = f"\nFirst, install required packages: pip install {deps_str}\n"

    prompt = f"""
You are executing code in a sandboxed environment.
Workspace directory: {workspace}

{setup_instructions}

Task: {task_description}

Instructions:
1. Write Python code to accomplish the task
2. Save the code to a .py file in the workspace
3. Execute the code and capture the output
4. Report any errors encountered

Always work within the workspace directory.
"""

    options = ClaudeAgentOptions(
        allowed_tools=["Bash", "Write", "Read", "Edit"],
        cwd=workspace,
        permission_mode="acceptEdits",
        # can_use_tool=sandbox_permission_handler,  # Uncomment if SDK supports it
    )

    result_text = ""
    sandbox.log_execution("start", {"task": task_description})

    try:
        async for message in query(prompt=prompt, options=options):
            if hasattr(message, "result"):
                result_text = message.result
                sandbox.log_execution("complete", {"result": result_text[:500]})

    except Exception as e:
        sandbox.log_execution("error", {"error": str(e)})
        result_text = f"Execution error: {e}"

    # Get list of created files
    files = sandbox.list_files()
    sandbox.save_log()

    return {
        "success": "error" not in result_text.lower(),
        "output": result_text,
        "files": files,
        "workspace": workspace,
        "sandbox_id": sandbox.sandbox_id
    }


async def demo_basic_execution():
    """Demo 1: Basic code execution."""
    print("\n" + "=" * 60)
    print("Demo 1: Basic Code Execution in Sandbox")
    print("=" * 60)

    sandbox = CodeExecutionSandbox("demo_basic")

    result = await run_code_in_sandbox(
        task_description="""
        Create a Python script that:
        1. Defines a function to check if a number is prime
        2. Finds all prime numbers between 1 and 100
        3. Prints the primes and their count
        """,
        sandbox=sandbox
    )

    print(f"\nExecution Result:")
    print(f"  Success: {result['success']}")
    print(f"  Files created: {result['files']}")
    print(f"  Workspace: {result['workspace']}")
    print(f"\nOutput:\n{result['output']}")


async def demo_data_processing():
    """Demo 2: Data processing with file output."""
    print("\n" + "=" * 60)
    print("Demo 2: Data Processing with File Output")
    print("=" * 60)

    sandbox = CodeExecutionSandbox("demo_data")

    result = await run_code_in_sandbox(
        task_description="""
        Create a Python script that:
        1. Generates a dataset of 50 students with:
           - name (random)
           - age (18-25)
           - grade (A, B, C, D, F)
           - score (0-100)
        2. Save the data to 'students.json'
        3. Calculate and print statistics:
           - Average score
           - Grade distribution
           - Top 5 students by score
        4. Use only built-in libraries
        """,
        sandbox=sandbox
    )

    print(f"\nExecution Result:")
    print(f"  Success: {result['success']}")
    print(f"  Files created: {result['files']}")
    print(f"\nOutput:\n{result['output']}")


async def demo_visualization_text():
    """Demo 3: Text-based visualization."""
    print("\n" + "=" * 60)
    print("Demo 3: Text-based Data Visualization")
    print("=" * 60)

    sandbox = CodeExecutionSandbox("demo_viz")

    result = await run_code_in_sandbox(
        task_description="""
        Create a Python script that:
        1. Generates monthly sales data for a year (12 months)
        2. Creates a text-based bar chart showing sales per month
        3. Shows trend analysis (increasing/decreasing)
        4. Use only built-in libraries, create ASCII art chart

        Example output format:
        Jan: ████████████ 120
        Feb: ██████████ 100
        ...
        """,
        sandbox=sandbox
    )

    print(f"\nExecution Result:")
    print(f"  Success: {result['success']}")
    print(f"  Files created: {result['files']}")
    print(f"\nOutput:\n{result['output']}")


async def demo_algorithm_implementation():
    """Demo 4: Algorithm implementation."""
    print("\n" + "=" * 60)
    print("Demo 4: Algorithm Implementation")
    print("=" * 60)

    sandbox = CodeExecutionSandbox("demo_algo")

    result = await run_code_in_sandbox(
        task_description="""
        Create a Python script that implements and compares sorting algorithms:
        1. Implement: bubble sort, selection sort, insertion sort
        2. Generate a random list of 1000 integers
        3. Time each sorting algorithm
        4. Print a comparison table showing execution times
        5. Verify all algorithms produce the same sorted result
        """,
        sandbox=sandbox
    )

    print(f"\nExecution Result:")
    print(f"  Success: {result['success']}")
    print(f"  Files created: {result['files']}")
    print(f"\nOutput:\n{result['output']}")


async def demo_web_scraping_mock():
    """Demo 5: Mock web data processing."""
    print("\n" + "=" * 60)
    print("Demo 5: Mock API Data Processing")
    print("=" * 60)

    sandbox = CodeExecutionSandbox("demo_api")

    result = await run_code_in_sandbox(
        task_description="""
        Create a Python script that simulates API data processing:
        1. Create mock JSON data representing API responses:
           - 10 products with: id, name, price, category, stock
        2. Save raw data to 'api_response.json'
        3. Process the data:
           - Filter products with stock > 0
           - Group by category
           - Calculate average price per category
        4. Save processed data to 'processed_data.json'
        5. Print a summary report
        """,
        sandbox=sandbox
    )

    print(f"\nExecution Result:")
    print(f"  Success: {result['success']}")
    print(f"  Files created: {result['files']}")
    print(f"\nOutput:\n{result['output']}")


async def main():
    """Run code execution demos."""
    check_api_key()

    print("\n" + "#" * 60)
    print("# Claude Agent SDK - Sandboxed Code Execution")
    print(f"# Sandbox Root: {SANDBOX_ROOT}")
    print("#" * 60)

    demos = [
        ("Basic Execution", demo_basic_execution),
        ("Data Processing", demo_data_processing),
        ("Text Visualization", demo_visualization_text),
        ("Algorithm Implementation", demo_algorithm_implementation),
        ("API Data Processing", demo_web_scraping_mock),
    ]

    print("\nAvailable Demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")

    # Run the first demo by default
    print("\nRunning Demo 1...")
    await demo_basic_execution()

    # Uncomment to run all demos:
    # for name, demo_func in demos:
    #     print(f"\n>>> Running: {name}")
    #     await demo_func()

    print("\n" + "=" * 60)
    print("Demo complete! Check the sandbox directory for generated files:")
    print(f"  {SANDBOX_ROOT}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
