# Claude Agent SDK Demo

A hands-on learning project for the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python).

## What is Claude Agent SDK?

Claude Agent SDK is a framework for building production AI agents using Claude. It's the programmatic version of Claude Code, providing:

- **Built-in tools**: File operations, code search, web capabilities, bash commands
- **Autonomous tool execution**: No need to implement your own tool loop
- **Sessions**: Maintain context across multiple queries
- **Hooks**: Monitor and control agent behavior
- **Subagents**: Delegate tasks to specialized agents
- **MCP Integration**: Connect to external systems

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Authentication

The SDK supports multiple authentication methods:

#### Option A: Google Vertex AI (Recommended for this project)

```bash
# .env file
CLAUDE_CODE_USE_VERTEX=1
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\credentials.json
```

#### Option B: Anthropic API

```bash
# .env file
ANTHROPIC_API_KEY=your-api-key-here
```

Get your API key from: https://platform.claude.com/

#### Option C: Amazon Bedrock

```bash
# .env file
CLAUDE_CODE_USE_BEDROCK=1
AWS_REGION=us-west-2
```

### 3. Run your first example

```bash
cd examples
python 01_basic_query.py
```

## Project Structure

```
claude_agent_sdk_demo/
├── examples/                    # Learning examples (start here!)
│   ├── 01_basic_query.py        # Simple query
│   ├── 02_file_operations.py    # Read, Write, Edit files
│   ├── 03_code_analysis.py      # Glob, Grep for code search
│   ├── 04_bash_commands.py      # Execute shell commands
│   ├── 05_interactive_session.py # Multi-turn conversations
│   ├── 06_session_resumption.py # Save and resume sessions
│   ├── 07_hooks_and_logging.py  # Monitor agent behavior
│   ├── 08_web_search.py         # WebSearch, WebFetch
│   ├── 09_subagents.py          # Delegate to specialized agents
│   └── 10_error_handling.py     # Production error patterns
├── projects/                    # Practical projects
│   └── code_analyzer/           # Code analysis agent
├── utils/                       # Shared utilities
│   ├── config.py                # Configuration
│   └── message_handler.py       # Message processing
├── .env.example                 # Environment template
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Examples Overview

| Example | Description | Tools Used |
|---------|-------------|------------|
| 01_basic_query | Simplest possible query | - |
| 02_file_operations | Create, read, edit files | Read, Write, Edit |
| 03_code_analysis | Search and analyze code | Glob, Grep, Read |
| 04_bash_commands | Execute shell commands | Bash |
| 05_interactive_session | Multi-turn conversation | Read, Glob, Grep |
| 06_session_resumption | Save/restore context | Read, Glob |
| 07_hooks_and_logging | Monitor tool usage | Glob, Read, Bash |
| 08_web_search | Search the web | WebSearch, WebFetch |
| 09_subagents | Delegate to specialists | Task, Read, Glob |
| 10_error_handling | Production patterns | Read, Glob |

## Key Concepts

### ClaudeAgentOptions

Configure agent behavior:

```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode="acceptEdits",  # Auto-approve file changes
    system_prompt="You are a helpful assistant",
    cwd="/path/to/project",
    max_turns=10,
)
```

### Permission Modes

- `interactive`: Require approval for each action (safest)
- `acceptEdits`: Auto-approve file changes
- `bypassPermissions`: Full access (use carefully)

### Available Tools

| Tool | Description |
|------|-------------|
| Read | Read file contents |
| Write | Create/overwrite files |
| Edit | Modify existing files |
| Glob | Find files by pattern |
| Grep | Search file contents |
| Bash | Execute shell commands |
| WebSearch | Search the web |
| WebFetch | Fetch URL content |
| AskUserQuestion | Request user input |
| Task | Spawn subagents |

## Resources

- [Official Documentation](https://platform.claude.com/docs/en/agent-sdk/overview)
- [GitHub Repository](https://github.com/anthropics/claude-agent-sdk-python)
- [Official Demos](https://github.com/anthropics/claude-agent-sdk-demos)
- [API Reference](https://platform.claude.com/)

## License

MIT - Feel free to use this for learning and building!
