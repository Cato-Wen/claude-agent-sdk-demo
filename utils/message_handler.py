"""Common message processing utilities."""

from typing import Any


def print_message(message: Any, verbose: bool = False):
    """Print agent messages in a readable format."""

    # Handle result messages (final output)
    if hasattr(message, "result"):
        print(f"\n{'='*50}")
        print("RESULT:")
        print(message.result)
        print('='*50)
        return

    # Handle assistant messages
    if hasattr(message, "content"):
        content = message.content
        if isinstance(content, str):
            print(f"Assistant: {content}")
        elif isinstance(content, list):
            for item in content:
                if hasattr(item, "text"):
                    print(f"Assistant: {item.text}")

    # Verbose mode: show all message details
    if verbose:
        print(f"[DEBUG] Message type: {type(message).__name__}")
        if hasattr(message, "__dict__"):
            for key, value in message.__dict__.items():
                if not key.startswith("_"):
                    print(f"  {key}: {value}")


def extract_session_id(message: Any) -> str | None:
    """Extract session ID from init message."""
    if hasattr(message, 'subtype') and message.subtype == 'init':
        return getattr(message, 'session_id', None)
    return None
