import argparse
import logging
from pathlib import Path

from config import DEFAULT_FOLDER, LOG_FILENAME
from duplicates import (
    display_duplicates,
    export_duplicates_to_csv,
    find_duplicates,
)
from organizer import organize_folder


def parse_arguments() -> argparse.Namespace:
    """Read command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Organize files, find duplicates "
            "or undo the latest organization."
        )
    )

    parser.add_argument(
        "--folder",
        type=Path,
        default=DEFAULT_FOLDER,
        help="Folder to process. Default: Downloads.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview an operation without moving files.",
    )

    action_group = parser.add_mutually_exclusive_group()

    action_group.add_argument(
        "--find-duplicates",
        action="store_true",
        help="Find duplicate files recursively.",
    )

    action_group.add_argument(
        "--undo",
        action="store_true",
        help="Undo the most recent organization.",
    )

    return parser.parse_args()


def configure_logging() -> None:
    """Configure terminal and file logging."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(
                LOG_FILENAME,
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
        force=True,
    )


def main() -> None:
    """Run the application."""

    arguments = parse_arguments()
    configure_logging()

    if arguments.undo:
        try:
            from history import undo_last_operation
        except ImportError as error:
            logging.error(
                "Undo module is unavailable: %s",
                error,
            )
            return

        if arguments.dry_run:
            logging.warning(
                "DRY RUN is enabled. Files will not be restored."
            )

        undo_last_operation(
            dry_run=arguments.dry_run
        )
        return

    selected_folder = (
        arguments.folder
        .expanduser()
        .resolve()
    )

    logging.info(
        "Selected folder: %s",
        selected_folder,
    )

    if arguments.find_duplicates:
        duplicate_groups = find_duplicates(
            selected_folder
        )

        display_duplicates(duplicate_groups)

        if duplicate_groups:
            export_duplicates_to_csv(
                duplicate_groups
            )

        return

    if arguments.dry_run:
        logging.warning(
            "DRY RUN is enabled. Files will not be moved."
        )

    movements = organize_folder(
        source_folder=selected_folder,
        dry_run=arguments.dry_run,
    )

    if movements and not arguments.dry_run:
        try:
            from history import record_operation
        except ImportError as error:
            logging.error(
                "Could not save movement history: %s",
                error,
            )
            return

        record_operation(movements)


if __name__ == "__main__":
    main()
