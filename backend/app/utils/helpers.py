import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def format_file_size(bytes_size: int) -> str:
    """Format bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"


def ensure_directory(path: str) -> str:
    """Ensure directory exists and return path."""
    os.makedirs(path, exist_ok=True)
    return path


def clean_text(text: str) -> str:
    """Clean text for processing."""
    return text.strip().lower() if text else ""
