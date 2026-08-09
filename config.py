import json
import logging
import sys
from pathlib import Path


def get_application_folder() -> Path:
    """
    Return the folder containing the application.

    This also works when the project is converted into an EXE.
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


APPLICATION_FOLDER = get_application_folder()

DEFAULT_FOLDER = Path.home() / "Downloads"

LOG_FILENAME = str(
    APPLICATION_FOLDER / "organizer.log"
)

DUPLICATES_REPORT_FILENAME = str(
    APPLICATION_FOLDER / "duplicates_report.csv"
)

HISTORY_FILENAME = str(
    APPLICATION_FOLDER / "move_history.json"
)

CONFIG_PATH = APPLICATION_FOLDER / "config.json"


DEFAULT_FILE_CATEGORIES: dict[str, set[str]] = {
    "Images": {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
        ".bmp",
    },
    "Documents": {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".odt",
    },
    "Spreadsheets": {
        ".xls",
        ".xlsx",
        ".csv",
    },
    "Presentations": {
        ".ppt",
        ".pptx",
    },
    "Archives": {
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
    },
    "Installers": {
        ".exe",
        ".msi",
    },
    "Videos": {
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".webm",
    },
    "Music": {
        ".mp3",
        ".wav",
        ".flac",
        ".m4a",
    },
    "Code": {
        ".py",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".java",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".json",
    },
}


def normalize_extension(
    extension: object,
) -> str | None:
    """Normalize an extension read from config.json."""

    if not isinstance(extension, str):
        return None

    normalized = extension.strip().lower()

    if not normalized:
        return None

    if not normalized.startswith("."):
        normalized = f".{normalized}"

    return normalized


def load_file_categories() -> dict[str, set[str]]:
    """
    Load file categories from config.json.

    Default categories are used when the configuration file is
    missing or contains invalid data.
    """

    if not CONFIG_PATH.exists():
        logging.warning(
            "Configuration file not found: %s. "
            "Default categories will be used.",
            CONFIG_PATH,
        )

        return {
            category: set(extensions)
            for category, extensions
            in DEFAULT_FILE_CATEGORIES.items()
        }

    try:
        config_text = CONFIG_PATH.read_text(
            encoding="utf-8"
        )

        config_data = json.loads(config_text)

    except OSError as error:
        logging.warning(
            "Could not read config.json: %s",
            error,
        )

        return {
            category: set(extensions)
            for category, extensions
            in DEFAULT_FILE_CATEGORIES.items()
        }

    except json.JSONDecodeError as error:
        logging.warning(
            "Invalid JSON in config.json: %s",
            error,
        )

        return {
            category: set(extensions)
            for category, extensions
            in DEFAULT_FILE_CATEGORIES.items()
        }

    categories_data = config_data.get("categories")

    if not isinstance(categories_data, dict):
        logging.warning(
            "The 'categories' section is missing "
            "or invalid in config.json."
        )

        return {
            category: set(extensions)
            for category, extensions
            in DEFAULT_FILE_CATEGORIES.items()
        }

    loaded_categories: dict[str, set[str]] = {}

    for category, extensions in categories_data.items():
        if not isinstance(category, str):
            continue

        category_name = category.strip()

        if not category_name:
            continue

        if not isinstance(extensions, list):
            continue

        normalized_extensions = {
            normalized
            for extension in extensions
            if (
                normalized := normalize_extension(extension)
            ) is not None
        }

        if normalized_extensions:
            loaded_categories[
                category_name
            ] = normalized_extensions

    if not loaded_categories:
        logging.warning(
            "No valid categories were found in config.json. "
            "Default categories will be used."
        )

        return {
            category: set(extensions)
            for category, extensions
            in DEFAULT_FILE_CATEGORIES.items()
        }

    return loaded_categories


FILE_CATEGORIES = load_file_categories()