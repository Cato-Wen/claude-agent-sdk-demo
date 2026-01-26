# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a demo/learning project for the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python), a Python framework for building production AI agents using Claude. The SDK provides programmatic access to Claude Code's capabilities including built-in tools, autonomous tool execution, sessions, hooks, and subagents.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run any example (from project root)
cd examples && python 01_basic_query.py

# Run the code analyzer project
cd projects/code_analyzer && python analyzer.py
```

## Authentication

Configure one of three authentication methods in `.env`:

1. **Anthropic API**: `ANTHROPIC_API_KEY=your-key`
2. **Google Vertex AI**: `CLAUDE_CODE_USE_VERTEX=1` + `GOOGLE_APPLICATION_CREDENTIALS=path/to/creds.json`
3. **Amazon Bedrock**: `CLAUDE_CODE_USE_BEDROCK=1` + AWS credentials

## Architecture

### Core SDK Pattern

All examples follow the same async streaming pattern:

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode="acceptEdits",  # Auto-approve file changes
    cwd="/path/to/project",
)

async for message in query(prompt="...", options=options):
    if hasattr(message, "result"):
        print(message.result)
```

### Directory Structure

- `examples/` - Learning examples (01-10) progressing from basic queries to advanced patterns
- `projects/code_analyzer/` - Practical code analysis agent implementation
- `utils/config.py` - Authentication checking and project paths
- `utils/message_handler.py` - Message processing helpers (`print_message`, `extract_session_id`)

### Key SDK Concepts

**Permission Modes:**
- `interactive` - Require approval for each action (safest)
- `acceptEdits` - Auto-approve file changes
- `bypassPermissions` - Full access (use carefully)

**Built-in Tools:** Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, AskUserQuestion, Task

**Hooks:** PreToolUse, PostToolUse, SessionStart, SessionEnd - callback functions to monitor/control agent behavior

**Subagents:** Define specialized agents via `agents` dict in options, invoke via Task tool. Each agent gets its own `description`, `tools`, and `system_prompt`.

**Sessions:** Capture `session_id` from init message, use `resume=session_id` in options to continue conversations with full context.
