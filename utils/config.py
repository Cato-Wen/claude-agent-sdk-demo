"""Shared configuration for Claude Agent SDK demos."""

import os
import platform
from pathlib import Path
from dotenv import load_dotenv

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"
PROJECTS_DIR = PROJECT_ROOT / "projects"

# Load environment variables from project root .env (override existing)
load_dotenv(PROJECT_ROOT / ".env", override=True)


def _convert_path_for_wsl(windows_path: str) -> str:
    """Convert Windows path to WSL path if running in WSL."""
    if not windows_path:
        return windows_path

    # Check if we're in WSL (Linux with access to /mnt/c)
    is_wsl = platform.system() == "Linux" and Path("/mnt/c").exists()

    if is_wsl and len(windows_path) >= 2 and windows_path[1] == ':':
        # Convert C:/path or C:\path to /mnt/c/path
        drive_letter = windows_path[0].lower()
        rest_of_path = windows_path[2:].replace('\\', '/')
        return f"/mnt/{drive_letter}{rest_of_path}"

    return windows_path


def check_api_key():
    """Check if authentication is properly configured."""
    # Check for Vertex AI
    if os.getenv("CLAUDE_CODE_USE_VERTEX") == "1":
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_path:
            raise EnvironmentError(
                "GOOGLE_APPLICATION_CREDENTIALS not set for Vertex AI. "
                "Set the path to your service account JSON file."
            )
        # Convert path for WSL if needed
        creds_path = _convert_path_for_wsl(creds_path)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

        if not Path(creds_path).exists():
            raise EnvironmentError(
                f"Google credentials file not found: {creds_path}"
            )
        print(f"Using Google Vertex AI")
        print(f"Credentials: {creds_path}")
        return True

    # Check for Bedrock
    if os.getenv("CLAUDE_CODE_USE_BEDROCK") == "1":
        print("Using Amazon Bedrock")
        return True

    # Default: Anthropic API
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise EnvironmentError(
            "No authentication configured. Set one of:\n"
            "  - ANTHROPIC_API_KEY (Anthropic API)\n"
            "  - CLAUDE_CODE_USE_VERTEX=1 + GOOGLE_APPLICATION_CREDENTIALS (Vertex AI)\n"
            "  - CLAUDE_CODE_USE_BEDROCK=1 (Amazon Bedrock)"
        )
    print("Using Anthropic API")
    return True
