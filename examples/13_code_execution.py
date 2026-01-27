"""
Example 13: Code Execution Demo
===============================
Demonstrates a sandboxed code execution pattern using Claude Agent SDK.
This simulates the code_execution tool from Anthropic API.

Features:
- Execute Python code in isolated environment
- Capture stdout, stderr, and return values
- Handle execution errors gracefully
- Support for data analysis tasks
"""

import asyncio
import sys
import tempfile
import os

sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from utils.config import check_api_key, PROJECT_ROOT


# Create a sandbox directory for code execution
SANDBOX_DIR = os.path.join(PROJECT_ROOT, "sandbox")
os.makedirs(SANDBOX_DIR, exist_ok=True)


async def execute_code_simple():
    """
    Simple code execution: Let Claude write and run Python code.
    """
    print("\n" + "=" * 60)
    print("Demo 1: Simple Code Execution")
    print("=" * 60)

    options = ClaudeAgentOptions(
        allowed_tools=["Bash", "Write", "Read"],
        cwd=SANDBOX_DIR,
        permission_mode="acceptEdits",
    )

    prompt = """
    Write a Python script that:
    1. Calculates prime numbers from 1 to 50
    2. Prints each prime number
    3. Shows the total count

    Save the script as prime_calculator.py and run it.
    """

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")


async def execute_code_data_analysis():
    """
    Data analysis: Generate and analyze sample data.
    """
    print("\n" + "=" * 60)
    print("Demo 2: Data Analysis with Code Execution")
    print("=" * 60)

    options = ClaudeAgentOptions(
        allowed_tools=["Bash", "Write", "Read"],
        cwd=SANDBOX_DIR,
        permission_mode="acceptEdits",
    )

    prompt = """
    Create a Python script that:
    1. Generates 100 random sales data points (date, product, amount)
    2. Calculates total sales, average, min, max
    3. Groups by product and shows summary statistics
    4. Uses only built-in libraries (random, statistics, collections)

    Save as sales_analysis.py and run it.
    """

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")


async def execute_code_with_output_file():
    """
    Code execution that produces output files (CSV, JSON).
    """
    print("\n" + "=" * 60)
    print("Demo 3: Code Execution with Output Files")
    print("=" * 60)

    options = ClaudeAgentOptions(
        allowed_tools=["Bash", "Write", "Read"],
        cwd=SANDBOX_DIR,
        permission_mode="acceptEdits",
    )

    prompt = """
    Create a Python script that:
    1. Generates a list of 20 fictional employees (name, department, salary)
    2. Saves the data to employees.json
    3. Reads back the JSON and prints a formatted table
    4. Uses only built-in libraries (json, random)

    Save the script as employee_generator.py and run it.
    Then show me the contents of employees.json.
    """

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")


async def execute_code_math_computation():
    """
    Mathematical computation demo.
    """
    print("\n" + "=" * 60)
    print("Demo 4: Mathematical Computation")
    print("=" * 60)

    options = ClaudeAgentOptions(
        allowed_tools=["Bash", "Write", "Read"],
        cwd=SANDBOX_DIR,
        permission_mode="acceptEdits",
    )

    prompt = """
    Create a Python script that:
    1. Implements the Fibonacci sequence up to n=20
    2. Calculates factorials from 1 to 10
    3. Computes the golden ratio approximation using Fibonacci numbers
    4. Shows all results in a nicely formatted output

    Save as math_demo.py and run it.
    """

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")


async def execute_code_interactive():
    """
    Interactive code execution: User provides the code to run.
    """
    print("\n" + "=" * 60)
    print("Demo 5: Interactive Code Execution")
    print("=" * 60)

    # User-provided code (simulating user input)
    user_code = '''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

# Test the function
test_data = [64, 34, 25, 12, 22, 11, 90]
print(f"Original: {test_data}")
sorted_data = bubble_sort(test_data.copy())
print(f"Sorted: {sorted_data}")
'''

    options = ClaudeAgentOptions(
        allowed_tools=["Bash", "Write", "Read"],
        cwd=SANDBOX_DIR,
        permission_mode="acceptEdits",
    )

    prompt = f"""
    Execute the following Python code and show me the output:

    ```python
{user_code}
    ```

    Save it as user_script.py and run it.
    """

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(f"\nResult:\n{message.result}")


async def main():
    """Run all code execution demos."""
    check_api_key()

    print("\n" + "#" * 60)
    print("# Claude Agent SDK - Code Execution Demo")
    print("# Sandbox Directory:", SANDBOX_DIR)
    print("#" * 60)

    # Run demos sequentially
    demos = [
        ("Simple Code Execution", execute_code_simple),
        ("Data Analysis", execute_code_data_analysis),
        ("Output Files", execute_code_with_output_file),
        ("Math Computation", execute_code_math_computation),
        ("Interactive Execution", execute_code_interactive),
    ]

    print("\nAvailable Demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")

    print("\nRunning Demo 1 (Simple Code Execution)...")
    print("To run other demos, modify the main() function.\n")

    # Run just the first demo by default
    await execute_code_simple()

    # Uncomment to run all demos:
    # for name, demo_func in demos:
    #     await demo_func()


if __name__ == "__main__":
    asyncio.run(main())
