import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from config import HISTORY_FILENAME


def load_history() -> list[dict]:
    """Load file movement history from JSON."""

    history_path = Path(HISTORY_FILENAME)

    if not history_path.exists():
        return []

    try:
        content = history_path.read_text(
            encoding="utf-8"
        )

        history = json.loads(content)

        if not isinstance(history, list):
            logging.warning(
                "History file has an invalid format."
            )
            return []

        return history

    except (OSError, json.JSONDecodeError) as error:
        logging.warning(
            "Could not read history file: %s",
            error,
        )
        return []


def save_history(history: list[dict]) -> bool:
    """Save file movement history to JSON."""

    history_path = Path(HISTORY_FILENAME)

    try:
        history_path.write_text(
            json.dumps(
                history,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    except OSError as error:
        logging.error(
            "Could not save history: %s",
            error,
        )
        return False

    return True


def record_operation(
    moved_files: list[tuple[Path, Path]],
) -> None:
    """Record one complete organization operation."""

    if not moved_files:
        return

    history = load_history()

    operation = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "moves": [
            {
                "source": str(source),
                "destination": str(destination),
            }
            for source, destination in moved_files
        ],
    }

    history.append(operation)

    if save_history(history):
        logging.info(
            "Saved %s movement(s) to history.",
            len(moved_files),
        )


def create_safe_restore_path(
    original_path: Path,
) -> Path:
    """
    Create a safe path for restoring a file.

    Existing files are never overwritten.
    """

    if not original_path.exists():
        return original_path

    counter = 1

    while True:
        candidate = original_path.with_name(
            f"{original_path.stem}_restored_{counter}"
            f"{original_path.suffix}"
        )

        if not candidate.exists():
            return candidate

        counter += 1


def undo_last_operation(
    dry_run: bool = False,
) -> int:
    """Undo the most recent organization operation."""

    history = load_history()

    if not history:
        logging.info(
            "There are no operations to undo."
        )
        return 0

    last_operation = history[-1]
    moves = last_operation.get("moves", [])

    if not isinstance(moves, list) or not moves:
        logging.warning(
            "The last history entry contains no movements."
        )
        return 0

    restored_count = 0
    failed_moves: list[dict] = []

    for movement in reversed(moves):
        try:
            original_path = Path(
                movement["source"]
            )
            current_path = Path(
                movement["destination"]
            )

        except (KeyError, TypeError):
            logging.warning(
                "Invalid movement entry in history."
            )
            failed_moves.append(movement)
            continue

        if not current_path.exists():
            logging.warning(
                "Cannot restore missing file: %s",
                current_path,
            )
            failed_moves.append(movement)
            continue

        restore_path = create_safe_restore_path(
            original_path
        )

        if dry_run:
            logging.info(
                "[DRY RUN] Restore: %s -> %s",
                current_path,
                restore_path,
            )
            restored_count += 1
            continue

        try:
            restore_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.move(
                str(current_path),
                str(restore_path),
            )

        except (PermissionError, OSError) as error:
            logging.error(
                "Could not restore %s: %s",
                current_path,
                error,
            )
            failed_moves.append(movement)
            continue

        logging.info(
            "Restored: %s -> %s",
            current_path,
            restore_path,
        )

        if restore_path != original_path:
            logging.warning(
                "Original path was occupied. "
                "File restored as: %s",
                restore_path,
            )

        restored_count += 1

    if dry_run:
        logging.info(
            "Undo preview completed. "
            "Files that would be restored: %s.",
            restored_count,
        )
        return restored_count

    if failed_moves:
        last_operation["moves"] = list(
            reversed(failed_moves)
        )
        history[-1] = last_operation
    else:
        history.pop()

    save_history(history)

    logging.info(
        "Undo completed. Restored files: %s.",
        restored_count,
    )

    return restored_count