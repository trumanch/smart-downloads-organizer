import csv
import hashlib
import logging
from collections import defaultdict
from pathlib import Path

from config import DUPLICATES_REPORT_FILENAME


DuplicateGroup = tuple[str, list[Path]]


def calculate_sha256(
    file_path: Path,
    chunk_size: int = 1024 * 1024,
) -> str | None:
    """Calculate the SHA-256 hash of a file."""

    hash_object = hashlib.sha256()

    try:
        with file_path.open("rb") as file:
            while chunk := file.read(chunk_size):
                hash_object.update(chunk)

    except PermissionError:
        logging.warning(
            "Permission denied while reading: %s",
            file_path,
        )
        return None

    except OSError as error:
        logging.warning(
            "Could not read %s: %s",
            file_path,
            error,
        )
        return None

    return hash_object.hexdigest()


def find_duplicates(
    source_folder: Path,
) -> list[DuplicateGroup]:
    """
    Find duplicate files recursively.

    Files are first grouped by size and then compared using SHA-256.
    """

    source_folder = source_folder.expanduser().resolve()

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

    files_by_size: dict[int, list[Path]] = defaultdict(list)

    for file_path in source_folder.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.is_symlink():
            continue

        try:
            file_size = file_path.stat().st_size
            files_by_size[file_size].append(file_path)

        except OSError as error:
            logging.warning(
                "Could not inspect %s: %s",
                file_path,
                error,
            )

    files_by_hash: dict[str, list[Path]] = defaultdict(list)

    for same_size_files in files_by_size.values():
        if len(same_size_files) < 2:
            continue

        for file_path in same_size_files:
            file_hash = calculate_sha256(file_path)

            if file_hash is not None:
                files_by_hash[file_hash].append(file_path)

    duplicate_groups = [
        (file_hash, file_paths)
        for file_hash, file_paths in files_by_hash.items()
        if len(file_paths) > 1
    ]

    return sorted(
        duplicate_groups,
        key=lambda group: (
            len(group[1]),
            group[0],
        ),
        reverse=True,
    )


def display_duplicates(
    duplicate_groups: list[DuplicateGroup],
) -> None:
    """Display duplicate groups in the terminal."""

    if not duplicate_groups:
        logging.info(
            "No duplicate files found."
        )
        return

    logging.info(
        "Found %s duplicate group(s).",
        len(duplicate_groups),
    )

    for group_number, (_, file_paths) in enumerate(
        duplicate_groups,
        start=1,
    ):
        logging.info(
            "Duplicate group %s: %s file(s)",
            group_number,
            len(file_paths),
        )

        for file_path in file_paths:
            logging.info(
                "  %s",
                file_path,
            )


def export_duplicates_to_csv(
    duplicate_groups: list[DuplicateGroup],
    report_path: Path | None = None,
) -> Path | None:
    """Export duplicate file information to a CSV report."""

    if report_path is None:
        report_path = Path(
            DUPLICATES_REPORT_FILENAME
        )

    try:
        with report_path.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(
                [
                    "Group",
                    "SHA-256",
                    "File size in bytes",
                    "File path",
                ]
            )

            for group_number, (
                file_hash,
                file_paths,
            ) in enumerate(
                duplicate_groups,
                start=1,
            ):
                for file_path in file_paths:
                    try:
                        file_size = file_path.stat().st_size
                    except OSError:
                        file_size = ""

                    writer.writerow(
                        [
                            group_number,
                            file_hash,
                            file_size,
                            str(file_path),
                        ]
                    )

    except OSError as error:
        logging.error(
            "Could not create duplicate report: %s",
            error,
        )
        return None

    resolved_report_path = report_path.resolve()

    logging.info(
        "Duplicate report created: %s",
        resolved_report_path,
    )

    return resolved_report_path