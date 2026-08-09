import logging
import shutil
from pathlib import Path

from config import FILE_CATEGORIES


def get_category(file_path: Path) -> str:
    """Return a category based on the file extension."""

    extension = file_path.suffix.lower()

    for category, extensions in FILE_CATEGORIES.items():
        if extension in extensions:
            return category

    return "Other"


def create_unique_path(
    destination: Path,
) -> Path:
    """Return a destination path that does not overwrite files."""

    if not destination.exists():
        return destination

    counter = 1

    while True:
        candidate = destination.with_name(
            f"{destination.stem}_{counter}"
            f"{destination.suffix}"
        )

        if not candidate.exists():
            return candidate

        counter += 1


def move_file(
    file_path: Path,
    source_folder: Path,
    dry_run: bool,
) -> Path | None:
    """
    Move one file into its category folder.

    Returns the destination path when successful.
    """

    category = get_category(file_path)
    category_folder = source_folder / category

    destination = create_unique_path(
        category_folder / file_path.name
    )

    if dry_run:
        logging.info(
            "[DRY RUN] %s -> %s",
            file_path,
            destination,
        )
        return destination

    try:
        category_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.move(
            str(file_path),
            str(destination),
        )

    except PermissionError:
        logging.error(
            "Permission denied: %s",
            file_path,
        )
        return None

    except OSError as error:
        logging.error(
            "Could not move %s: %s",
            file_path,
            error,
        )
        return None

    logging.info(
        "Moved: %s -> %s",
        file_path,
        destination,
    )

    return destination


def organize_folder(
    source_folder: Path,
    dry_run: bool = False,
) -> list[tuple[Path, Path]]:
    """
    Organize files located directly in a folder.

    Returns a list containing source and destination paths.
    """

    source_folder = (
        source_folder
        .expanduser()
        .resolve()
    )

    if not source_folder.exists():
        logging.error(
            "Folder not found: %s",
            source_folder,
        )
        return []

    if not source_folder.is_dir():
        logging.error(
            "The selected path is not a folder: %s",
            source_folder,
        )
        return []

    files = [
        item
        for item in source_folder.iterdir()
        if item.is_file()
        and not item.is_symlink()
    ]

    if not files:
        logging.info(
            "No files found in: %s",
            source_folder,
        )
        return []

    logging.info(
        "Found %s file(s) in %s.",
        len(files),
        source_folder,
    )

    movements: list[tuple[Path, Path]] = []

    for file_path in files:
        destination = move_file(
            file_path=file_path,
            source_folder=source_folder,
            dry_run=dry_run,
        )

        if destination is not None:
            movements.append(
                (file_path, destination)
            )

    if dry_run:
        logging.info(
            "Dry run completed. "
            "Planned movements: %s.",
            len(movements),
        )
    else:
        logging.info(
            "Organization completed. "
            "Moved files: %s.",
            len(movements),
        )

    return movements