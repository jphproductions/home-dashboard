"""Utility for safely updating .env file with new configuration values."""

from pathlib import Path

from home_dashboard.logging_config import get_logger

logger = get_logger(__name__)


def update_env_file(env_path: Path, key: str, value: str) -> None:
    """Update or add a key-value pair in .env file.

    Args:
        env_path: Path to .env file
        key: Environment variable name (e.g., "SPOTIFY_REFRESH_TOKEN")
        value: New value for the variable

    Raises:
        FileNotFoundError: If .env file doesn't exist
        PermissionError: If .env file is not writable
        ValueError: If key contains invalid characters
    """
    # Validate key format
    if not key or "=" in key or "\n" in key:
        raise ValueError(f"Invalid environment variable key: {key}")

    if not env_path.exists():
        raise FileNotFoundError(f".env file not found at {env_path}")

    # Read current content
    lines = env_path.read_text(encoding="utf-8").splitlines()

    # Find and update the key
    updated = False
    for i, line in enumerate(lines):
        # Skip comments and empty lines
        if line.strip().startswith("#") or not line.strip():
            continue

        # Check if this line contains our key
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            logger.info(f"Updated {key} in .env file")
            break

    # If key not found, append it
    if not updated:
        # Add blank line if file doesn't end with one
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(f"# Auto-saved {key}")
        lines.append(f"{key}={value}")
        logger.info(f"Added {key} to .env file")

    # Write back to file
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_env_path() -> Path:
    """Get path to .env file in project root.

    Returns:
        Path to .env file

    Note:
        From home_dashboard/utils/env_updater.py
        Navigate to project root: ../../.env
    """
    return Path(__file__).parent.parent.parent / ".env"
