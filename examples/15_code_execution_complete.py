"""
Example 15: Complete Code Execution Framework
=============================================
A complete code execution framework that closely mimics
Anthropic API's code_execution tool.

Features:
- CodeExecutor class with clean API
- Automatic file tracking
- Execution timeout support
- Structured results (stdout, stderr, files, errors)
- Session management for multi-turn execution
- Pre-installed package simulation
"""

import asyncio
import sys
import os
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT


# ============================================================
# Data Structures
# ============================================================

class ExecutionStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result of code execution, similar to Anthropic API response."""
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    return_value: Any = None
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    execution_time_ms: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        result = asdict(self)
        result["status"] = self.status.value
        return result

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class CodeExecutionRequest:
    """Request for code execution."""
    code: Optional[str] = None  # Direct code to execute
    task: Optional[str] = None  # Natural language task description
    language: str = "python"
    timeout_ms: int = 60000
    packages: List[str] = field(default_factory=list)


# ============================================================
# Code Executor Class
# ============================================================

class CodeExecutor:
    """
    Code execution engine using Claude Agent SDK.
    Mimics Anthropic API's code_execution tool behavior.
    """

    SANDBOX_ROOT = os.path.join(PROJECT_ROOT, "sandbox", "executor")

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize a code execution session.

        Args:
            session_id: Optional session ID for resuming sessions
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.workspace = os.path.join(self.SANDBOX_ROOT, self.session_id)
        os.makedirs(self.workspace, exist_ok=True)

        self.execution_history: List[Dict] = []
        self._files_before: set = set()

    def _snapshot_files(self) -> set:
        """Take a snapshot of files in workspace."""
        files = set()
        if os.path.exists(self.workspace):
            for root, _, filenames in os.walk(self.workspace):
                for f in filenames:
                    path = os.path.join(root, f)
                    rel_path = os.path.relpath(path, self.workspace)
                    files.add(rel_path)
        return files

    def _detect_file_changes(self, before: set, after: set) -> tuple:
        """Detect created and modified files."""
        created = list(after - before)
        # For simplicity, we don't track modifications in this demo
        modified = []
        return created, modified

    async def execute(self, request: CodeExecutionRequest) -> ExecutionResult:
        """
        Execute code or a task.

        Args:
            request: CodeExecutionRequest with code or task

        Returns:
            ExecutionResult with execution details
        """
        start_time = time.time()
        self._files_before = self._snapshot_files()

        # Build prompt based on request type
        if request.code:
            prompt = self._build_code_prompt(request)
        elif request.task:
            prompt = self._build_task_prompt(request)
        else:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error_message="Either 'code' or 'task' must be provided"
            )

        # Configure Claude Agent SDK
        options = ClaudeAgentOptions(
            allowed_tools=["Bash", "Write", "Read", "Edit"],
            cwd=self.workspace,
            permission_mode="acceptEdits",
        )

        # Execute
        try:
            output_text = ""
            async for message in query(prompt=prompt, options=options):
                if hasattr(message, "result"):
                    output_text = message.result

            # Detect file changes
            files_after = self._snapshot_files()
            created, modified = self._detect_file_changes(self._files_before, files_after)

            # Calculate execution time
            execution_time = int((time.time() - start_time) * 1000)

            # Parse output for errors
            has_error = any(word in output_text.lower() for word in ["error", "exception", "traceback"])

            result = ExecutionResult(
                status=ExecutionStatus.ERROR if has_error else ExecutionStatus.SUCCESS,
                stdout=output_text,
                files_created=created,
                files_modified=modified,
                execution_time_ms=execution_time,
                error_message=output_text if has_error else None
            )

        except asyncio.TimeoutError:
            result = ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                error_message=f"Execution timed out after {request.timeout_ms}ms"
            )
        except Exception as e:
            result = ExecutionResult(
                status=ExecutionStatus.ERROR,
                error_message=str(e)
            )

        # Record in history
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "request": asdict(request),
            "result": result.to_dict()
        })

        return result

    def _build_code_prompt(self, request: CodeExecutionRequest) -> str:
        """Build prompt for direct code execution."""
        packages_instruction = ""
        if request.packages:
            pkg_list = " ".join(request.packages)
            packages_instruction = f"\nFirst install packages: pip install {pkg_list}\n"

        return f"""
Execute the following Python code in the workspace directory: {self.workspace}
{packages_instruction}

```python
{request.code}
```

Instructions:
1. Save the code to a file named 'script.py'
2. Run the script using: python script.py
3. Capture and report all output
4. If there are errors, report them clearly
"""

    def _build_task_prompt(self, request: CodeExecutionRequest) -> str:
        """Build prompt for task-based execution."""
        packages_instruction = ""
        if request.packages:
            pkg_list = " ".join(request.packages)
            packages_instruction = f"\nAvailable packages to install if needed: {pkg_list}\n"

        return f"""
You are a code execution assistant working in: {self.workspace}
{packages_instruction}

Task: {request.task}

Instructions:
1. Write Python code to accomplish the task
2. Save code to appropriately named .py file(s)
3. Execute the code
4. Report all output and any files created
5. If creating data files, use JSON format when possible
"""

    def list_files(self) -> List[str]:
        """List all files in the workspace."""
        return list(self._snapshot_files())

    def read_file(self, filename: str) -> Optional[str]:
        """Read a file from the workspace."""
        filepath = os.path.join(self.workspace, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return f.read()
        return None

    def get_history(self) -> List[Dict]:
        """Get execution history."""
        return self.execution_history

    def cleanup(self):
        """Clean up the workspace (optional)."""
        import shutil
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)


# ============================================================
# High-Level API Functions
# ============================================================

async def execute_code(
    code: str,
    packages: Optional[List[str]] = None,
    timeout_ms: int = 60000
) -> ExecutionResult:
    """
    Convenience function to execute Python code.

    Args:
        code: Python code to execute
        packages: Optional list of pip packages to install
        timeout_ms: Execution timeout in milliseconds

    Returns:
        ExecutionResult
    """
    executor = CodeExecutor()
    request = CodeExecutionRequest(
        code=code,
        packages=packages or [],
        timeout_ms=timeout_ms
    )
    return await executor.execute(request)


async def execute_task(
    task: str,
    packages: Optional[List[str]] = None,
    timeout_ms: int = 60000
) -> ExecutionResult:
    """
    Convenience function to execute a natural language task.

    Args:
        task: Task description in natural language
        packages: Optional list of pip packages to install
        timeout_ms: Execution timeout in milliseconds

    Returns:
        ExecutionResult
    """
    executor = CodeExecutor()
    request = CodeExecutionRequest(
        task=task,
        packages=packages or [],
        timeout_ms=timeout_ms
    )
    return await executor.execute(request)


# ============================================================
# Demo Functions
# ============================================================

async def demo_direct_code_execution():
    """Demo: Execute code directly."""
    print("\n" + "=" * 60)
    print("Demo 1: Direct Code Execution")
    print("=" * 60)

    code = '''
import math

def calculate_circle_properties(radius):
    """Calculate properties of a circle."""
    area = math.pi * radius ** 2
    circumference = 2 * math.pi * radius
    return {
        "radius": radius,
        "area": round(area, 4),
        "circumference": round(circumference, 4)
    }

# Test with different radii
radii = [1, 2, 5, 10]
print("Circle Properties Calculator")
print("-" * 40)

for r in radii:
    props = calculate_circle_properties(r)
    print(f"Radius: {props['radius']:>5}")
    print(f"  Area: {props['area']:>10}")
    print(f"  Circumference: {props['circumference']:>10}")
    print()
'''

    result = await execute_code(code)

    print(f"\nStatus: {result.status.value}")
    print(f"Execution Time: {result.execution_time_ms}ms")
    print(f"Files Created: {result.files_created}")
    print(f"\nOutput:\n{result.stdout}")


async def demo_task_execution():
    """Demo: Execute a natural language task."""
    print("\n" + "=" * 60)
    print("Demo 2: Natural Language Task Execution")
    print("=" * 60)

    task = """
    Create a password generator that:
    1. Generates secure passwords of specified length
    2. Includes uppercase, lowercase, numbers, and symbols
    3. Generates 5 passwords of length 16
    4. Saves the passwords to 'passwords.txt'
    5. Prints the passwords to the console
    """

    result = await execute_task(task)

    print(f"\nStatus: {result.status.value}")
    print(f"Execution Time: {result.execution_time_ms}ms")
    print(f"Files Created: {result.files_created}")
    print(f"\nOutput:\n{result.stdout}")


async def demo_data_analysis():
    """Demo: Data analysis task."""
    print("\n" + "=" * 60)
    print("Demo 3: Data Analysis Task")
    print("=" * 60)

    task = """
    Perform a statistical analysis:
    1. Generate 1000 random numbers from a normal distribution (mean=50, std=10)
    2. Calculate: mean, median, mode, std deviation, variance
    3. Find: min, max, range, quartiles (Q1, Q2, Q3)
    4. Create a text-based histogram showing the distribution
    5. Save results to 'statistics_report.json'
    """

    result = await execute_task(task)

    print(f"\nStatus: {result.status.value}")
    print(f"Execution Time: {result.execution_time_ms}ms")
    print(f"Files Created: {result.files_created}")
    print(f"\nOutput:\n{result.stdout}")


async def demo_session_execution():
    """Demo: Multi-turn session execution."""
    print("\n" + "=" * 60)
    print("Demo 4: Multi-Turn Session Execution")
    print("=" * 60)

    # Create a persistent executor
    executor = CodeExecutor(session_id="multi_turn_demo")

    # First execution: Create data
    print("\n--- Step 1: Create Data ---")
    result1 = await executor.execute(CodeExecutionRequest(
        task="Create a JSON file 'inventory.json' with 10 products (id, name, price, quantity)"
    ))
    print(f"Status: {result1.status.value}")
    print(f"Files: {result1.files_created}")

    # Second execution: Analyze data
    print("\n--- Step 2: Analyze Data ---")
    result2 = await executor.execute(CodeExecutionRequest(
        task="Read 'inventory.json', calculate total inventory value, find most expensive product"
    ))
    print(f"Status: {result2.status.value}")
    print(f"Output:\n{result2.stdout}")

    # Third execution: Generate report
    print("\n--- Step 3: Generate Report ---")
    result3 = await executor.execute(CodeExecutionRequest(
        task="Create a summary report 'report.txt' with all inventory statistics"
    ))
    print(f"Status: {result3.status.value}")
    print(f"All files in workspace: {executor.list_files()}")

    # Show history
    print("\n--- Execution History ---")
    for i, entry in enumerate(executor.get_history(), 1):
        print(f"{i}. {entry['timestamp']}: {entry['result']['status']}")


async def demo_error_handling():
    """Demo: Error handling."""
    print("\n" + "=" * 60)
    print("Demo 5: Error Handling")
    print("=" * 60)

    # Code with intentional error
    code_with_error = '''
# This code has an intentional error
result = 10 / 0  # Division by zero
print(result)
'''

    result = await execute_code(code_with_error)

    print(f"\nStatus: {result.status.value}")
    print(f"Error Message: {result.error_message[:200] if result.error_message else 'None'}...")


async def demo_file_generation():
    """Demo: Multiple file generation."""
    print("\n" + "=" * 60)
    print("Demo 6: Multiple File Generation")
    print("=" * 60)

    task = """
    Create a simple project structure:
    1. Create 'config.json' with app settings (name, version, debug mode)
    2. Create 'main.py' that reads config and prints a welcome message
    3. Create 'utils.py' with a helper function to format text
    4. Run main.py to demonstrate the project works
    """

    executor = CodeExecutor(session_id="project_demo")
    result = await executor.execute(CodeExecutionRequest(task=task))

    print(f"\nStatus: {result.status.value}")
    print(f"Files Created: {result.files_created}")
    print(f"\nWorkspace contents:")
    for f in executor.list_files():
        print(f"  - {f}")

    # Show file contents
    print("\n--- config.json ---")
    content = executor.read_file("config.json")
    if content:
        print(content)


# ============================================================
# Main
# ============================================================

async def main():
    """Run all demos."""
    check_api_key()

    print("\n" + "#" * 60)
    print("# Complete Code Execution Framework Demo")
    print(f"# Sandbox: {CodeExecutor.SANDBOX_ROOT}")
    print("#" * 60)

    demos = [
        ("Direct Code Execution", demo_direct_code_execution),
        ("Task Execution", demo_task_execution),
        ("Data Analysis", demo_data_analysis),
        ("Session Execution", demo_session_execution),
        ("Error Handling", demo_error_handling),
        ("File Generation", demo_file_generation),
    ]

    print("\nAvailable Demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")

    # Run first demo
    print("\n" + "=" * 60)
    print("Running Demo 1: Direct Code Execution")
    print("=" * 60)
    await demo_direct_code_execution()

    # Uncomment to run all:
    # for name, demo_func in demos:
    #     await demo_func()


if __name__ == "__main__":
    asyncio.run(main())
