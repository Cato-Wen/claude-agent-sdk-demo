"""Message tracking utility for analyzing LLM behavior.

Captures all messages from query() and saves them to JSON for analysis.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator
from dataclasses import dataclass, field, asdict


@dataclass
class TrackedMessage:
    """A single tracked message with metadata."""
    index: int
    timestamp: str
    message_type: str
    data: dict = field(default_factory=dict)


class MessageTracker:
    """Tracks and saves all messages from Claude Agent SDK queries.

    Usage:
        tracker = MessageTracker("my_analysis")

        async for message in query(prompt="...", options=options):
            tracker.track(message)
            # your normal message handling...

        tracker.save()  # Saves to logs/my_analysis_20240128_143052.json
    """

    def __init__(self, name: str = "query", output_dir: str | Path = None):
        """Initialize tracker.

        Args:
            name: Name prefix for the output file
            output_dir: Directory to save logs (default: PROJECT_ROOT/logs)
        """
        self.name = name
        self.messages: list[TrackedMessage] = []
        self.start_time = datetime.now()
        self._index = 0

        # Set output directory
        if output_dir is None:
            from utils.config import PROJECT_ROOT
            output_dir = PROJECT_ROOT / "logs"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def track(self, message: Any) -> Any:
        """Track a message and return it unchanged (for pass-through usage).

        Args:
            message: The message object from query()

        Returns:
            The same message (allows chaining)
        """
        tracked = TrackedMessage(
            index=self._index,
            timestamp=datetime.now().isoformat(),
            message_type=type(message).__name__,
            data=self._serialize_message(message)
        )
        self.messages.append(tracked)
        self._index += 1
        return message

    def _serialize_message(self, message: Any) -> dict:
        """Convert message object to serializable dict."""
        result = {}

        # Try to get all attributes
        if hasattr(message, "__dict__"):
            for key, value in message.__dict__.items():
                if key.startswith("_"):
                    continue
                result[key] = self._serialize_value(value)

        # Also check for common known attributes
        for attr in ["result", "content", "subtype", "session_id", "tool_name",
                     "tool_input", "tool_output", "error", "type", "role"]:
            if hasattr(message, attr) and attr not in result:
                result[attr] = self._serialize_value(getattr(message, attr))

        return result

    def _serialize_value(self, value: Any) -> Any:
        """Recursively serialize a value to JSON-compatible format."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif hasattr(value, "__dict__"):
            # Nested object
            return {k: self._serialize_value(v)
                    for k, v in value.__dict__.items()
                    if not k.startswith("_")}
        else:
            # Fallback to string representation
            return str(value)

    def save(self, filename: str = None) -> Path:
        """Save all tracked messages to JSON file.

        Args:
            filename: Optional custom filename (without extension)

        Returns:
            Path to the saved file
        """
        if filename is None:
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"{self.name}_{timestamp}"

        filepath = self.output_dir / f"{filename}.json"

        output = {
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_messages": len(self.messages),
            "messages": [asdict(m) for m in self.messages]
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n[MessageTracker] Saved {len(self.messages)} messages to: {filepath}")
        return filepath

    def get_summary(self) -> dict:
        """Get a summary of tracked messages by type."""
        summary = {}
        for msg in self.messages:
            msg_type = msg.message_type
            summary[msg_type] = summary.get(msg_type, 0) + 1
        return summary

    def print_summary(self):
        """Print a summary of tracked messages."""
        print(f"\n[MessageTracker] Summary for '{self.name}':")
        print(f"  Total messages: {len(self.messages)}")
        print(f"  Message types:")
        for msg_type, count in sorted(self.get_summary().items()):
            print(f"    - {msg_type}: {count}")


async def tracked_query(prompt: str, options=None, tracker_name: str = "query",
                        output_dir: str | Path = None) -> AsyncIterator[Any]:
    """Wrapper around query() that automatically tracks all messages.

    Usage:
        async for message in tracked_query("What is Python?", name="python_query"):
            if hasattr(message, "result"):
                print(message.result)
        # Automatically saves to logs/python_query_YYYYMMDD_HHMMSS.json

    Args:
        prompt: The query prompt
        options: ClaudeAgentOptions
        tracker_name: Name prefix for the output file
        output_dir: Directory to save logs

    Yields:
        Messages from query()
    """
    from claude_agent_sdk import query

    tracker = MessageTracker(name=tracker_name, output_dir=output_dir)

    try:
        async for message in query(prompt=prompt, options=options):
            tracker.track(message)
            yield message
    finally:
        tracker.print_summary()
        tracker.save()
