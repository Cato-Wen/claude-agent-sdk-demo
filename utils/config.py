"""Shared configuration for Claude Agent SDK demos."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"
PROJECTS_DIR = PROJECT_ROOT / "projects"

# Load environment variables from project root .env (override existing)
load_dotenv(PROJECT_ROOT / ".env", override=True)


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
