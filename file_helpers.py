import logging
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_file_content(file_path: Path, resource_type: str = "file") -> str:
    """Load file content with enhanced error handling and validation."""
    if not file_path.exists():
        logger.warning(f"{resource_type.capitalize()} file not found: {file_path}")
        raise FileNotFoundError(f"{resource_type.capitalize()} file not found: {file_path} (expected in {file_path.parent.name}/)")

    if not file_path.is_file():
        logger.warning(f"Path is not a file: {file_path}")
        raise FileNotFoundError(f"Path is not a file: {file_path}")

    try:
        content = file_path.read_text(encoding="utf-8")
        if not content.strip():
            logger.warning(f"Empty {resource_type} file: {file_path.name}")
            raise ValueError(f"{resource_type.capitalize()} file exists but is empty: {file_path.name}")
        return content
    except UnicodeDecodeError as e:
        logger.error(f"Unable to decode {resource_type} file {file_path.name}: {e}")
        raise UnicodeDecodeError(f"Unable to decode {resource_type} file {file_path.name}: {e}")
    except Exception as e:
        logger.error(f"Error reading {resource_type} file {file_path.name}: {e}")
        raise IOError(f"Error reading {resource_type} file {file_path.name}: {e}")

def get_available_files(directory: Path, extension: str = "") -> List[str]:
    """Get list of available files in a directory. If extension is provided, filter by extension; otherwise, return all files."""
    if not directory.exists():
        return []
    if extension:
        return [f.stem for f in directory.glob(f"*{extension}") if f.is_file()]
    else:
        return [f.stem for f in directory.iterdir() if f.is_file()]
