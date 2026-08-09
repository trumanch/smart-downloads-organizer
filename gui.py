import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from config import DEFAULT_FOLDER, LOG_FILENAME
from duplicates import (
    display_duplicates,
    export_duplicates_to_csv,
    find_duplicates,
)
from history import record_operation, undo_last_operation
from organizer import organize_folder


class TkinterLogHandler(logging.Handler):
    """Send log messages safely to a Tkinter text widget."""

    def __init__(
        self,
        root: tk.Tk,
        text_widget: ScrolledText,
    ) -> None:
        super().__init__()
        self.root = root
        self.text_widget = text_widget

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)

        self.root.after(
            0,
            self._append_message,
            message,
        )

    def _append_message(self, message: str) -> None:
        self.text_widget.configure(state="normal")
        self.text_widget.insert(
            tk.END,
            message + "\n",
        )
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")


class FileOrganizerApp:
    """Graphical interface for Smart Downloads Organizer."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root

        self.root.title(
            "Smart Downloads Organizer"
        )
        self.root.geometry("850x600")
        self.root.minsize(700, 500)

        self.folder_variable = tk.StringVar(
            value=str(DEFAULT_FOLDER)
        )

        self.dry_run_variable = tk.BooleanVar(
            value=True
        )

        self.status_variable = tk.StringVar(
            value="Ready"
        )

        self.action_buttons: list[ttk.Button] = []

        self._create_widgets()
        self._configure_logging()

    def _create_widgets(self) -> None:
        """Create all interface elements."""

        main_frame = ttk.Frame(
            self.root,
            padding=15,
        )
        main_frame.pack(
            fill=tk.BOTH,
            expand=True,
        )

        title_label = ttk.Label(
            main_frame,
            text="Smart Downloads Organizer",
            font=("Segoe UI", 18, "bold"),
        )
        title_label.pack(
            anchor=tk.W,
            pady=(0, 15),
        )

        folder_frame = ttk.LabelFrame(
            main_frame,
            text="Folder",
            padding=10,
        )
        folder_frame.pack(
            fill=tk.X,
            pady=(0, 10),
        )

        folder_entry = ttk.Entry(
            folder_frame,
            textvariable=self.folder_variable,
        )
        folder_entry.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=(0, 10),
        )

        browse_button = ttk.Button(
            folder_frame,
            text="Browse",
            command=self.select_folder,
        )
        browse_button.pack(side=tk.RIGHT)

        options_frame = ttk.Frame(main_frame)
        options_frame.pack(
            fill=tk.X,
            pady=(0, 10),
        )

        dry_run_checkbox = ttk.Checkbutton(
            options_frame,
            text="Dry run — preview without moving files",
            variable=self.dry_run_variable,
        )
        dry_run_checkbox.pack(side=tk.LEFT)

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(
            fill=tk.X,
            pady=(0, 10),
        )

        organize_button = ttk.Button(
            buttons_frame,
            text="Organize Files",
            command=self.start_organization,
        )
        organize_button.pack(
            side=tk.LEFT,
            padx=(0, 8),
        )

        duplicates_button = ttk.Button(
            buttons_frame,
            text="Find Duplicates",
            command=self.start_duplicate_search,
        )
        duplicates_button.pack(
            side=tk.LEFT,
            padx=(0, 8),
        )

        undo_button = ttk.Button(
            buttons_frame,
            text="Undo Last Operation",
            command=self.start_undo,
        )
        undo_button.pack(
            side=tk.LEFT,
            padx=(0, 8),
        )

        clear_button = ttk.Button(
            buttons_frame,
            text="Clear Log",
            command=self.clear_log,
        )
        clear_button.pack(side=tk.RIGHT)

        self.action_buttons = [
            organize_button,
            duplicates_button,
            undo_button,
        ]

        log_frame = ttk.LabelFrame(
            main_frame,
            text="Activity Log",
            padding=10,
        )
        log_frame.pack(
            fill=tk.BOTH,
            expand=True,
        )

        self.log_text = ScrolledText(
            log_frame,
            wrap=tk.WORD,
            state="disabled",
            font=("Consolas", 10),
        )
        self.log_text.pack(
            fill=tk.BOTH,
            expand=True,
        )

        status_frame = ttk.Frame(main_frame)
        status_frame.pack(
            fill=tk.X,
            pady=(10, 0),
        )

        self.progress_bar = ttk.Progressbar(
            status_frame,
            mode="indeterminate",
            length=150,
        )
        self.progress_bar.pack(
            side=tk.RIGHT,
        )

        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_variable,
        )
        status_label.pack(side=tk.LEFT)

    def _configure_logging(self) -> None:
        """Configure file and GUI logging."""

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        file_handler = logging.FileHandler(
            LOG_FILENAME,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        gui_handler = TkinterLogHandler(
            self.root,
            self.log_text,
        )
        gui_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(gui_handler)

    def select_folder(self) -> None:
        """Open a folder selection dialog."""

        selected_folder = filedialog.askdirectory(
            initialdir=self.folder_variable.get(),
            title="Select folder",
        )

        if selected_folder:
            self.folder_variable.set(
                selected_folder
            )

    def get_selected_folder(self) -> Path | None:
        """Validate and return the selected folder."""

        folder_text = self.folder_variable.get().strip()

        if not folder_text:
            messagebox.showerror(
                "Folder required",
                "Please select a folder.",
            )
            return None

        folder_path = (
            Path(folder_text)
            .expanduser()
            .resolve()
        )

        if not folder_path.exists():
            messagebox.showerror(
                "Folder not found",
                f"The folder does not exist:\n{folder_path}",
            )
            return None

        if not folder_path.is_dir():
            messagebox.showerror(
                "Invalid path",
                "The selected path is not a folder.",
            )
            return None

        return folder_path

    def set_busy(
        self,
        busy: bool,
        status: str,
    ) -> None:
        """Enable or disable action controls."""

        self.status_variable.set(status)

        button_state = (
            tk.DISABLED
            if busy
            else tk.NORMAL
        )

        for button in self.action_buttons:
            button.configure(
                state=button_state
            )

        if busy:
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()

    def run_background(
        self,
        operation,
        status: str,
    ) -> None:
        """Run an operation without freezing the interface."""

        self.set_busy(
            busy=True,
            status=status,
        )

        thread = threading.Thread(
            target=self._background_wrapper,
            args=(operation,),
            daemon=True,
        )
        thread.start()

    def _background_wrapper(
        self,
        operation,
    ) -> None:
        """Handle background operation errors."""

        try:
            operation()

        except Exception:
            logging.exception(
                "Unexpected application error."
            )

            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Error",
                    "An unexpected error occurred. "
                    "Check the activity log.",
                ),
            )

        finally:
            self.root.after(
                0,
                lambda: self.set_busy(
                    busy=False,
                    status="Ready",
                ),
            )

    def start_organization(self) -> None:
        """Validate input and start file organization."""

        selected_folder = self.get_selected_folder()

        if selected_folder is None:
            return

        dry_run = self.dry_run_variable.get()

        if not dry_run:
            confirmed = messagebox.askyesno(
                "Confirm organization",
                "Files will be moved into category folders.\n\n"
                "Continue?",
            )

            if not confirmed:
                return

        self.run_background(
            operation=lambda: self.organize_files(
                selected_folder,
                dry_run,
            ),
            status="Organizing files...",
        )

    def organize_files(
        self,
        selected_folder: Path,
        dry_run: bool,
    ) -> None:
        """Organize the selected folder."""

        logging.info(
            "Selected folder: %s",
            selected_folder,
        )

        if dry_run:
            logging.warning(
                "DRY RUN is enabled. "
                "Files will not be moved."
            )

        movements = organize_folder(
            source_folder=selected_folder,
            dry_run=dry_run,
        )

        if movements and not dry_run:
            record_operation(movements)

        logging.info(
            "Organization task finished."
        )

    def start_duplicate_search(self) -> None:
        """Start duplicate file search."""

        selected_folder = self.get_selected_folder()

        if selected_folder is None:
            return

        self.run_background(
            operation=lambda: self.search_duplicates(
                selected_folder
            ),
            status="Searching for duplicates...",
        )

    def search_duplicates(
        self,
        selected_folder: Path,
    ) -> None:
        """Find and report duplicate files."""

        logging.info(
            "Searching for duplicates in: %s",
            selected_folder,
        )

        duplicate_groups = find_duplicates(
            selected_folder
        )

        display_duplicates(
            duplicate_groups
        )

        if duplicate_groups:
            report_path = export_duplicates_to_csv(
                duplicate_groups
            )

            if report_path is not None:
                logging.info(
                    "CSV report saved to: %s",
                    report_path,
                )

        logging.info(
            "Duplicate search finished."
        )

    def start_undo(self) -> None:
        """Start undo operation."""

        dry_run = self.dry_run_variable.get()

        if not dry_run:
            confirmed = messagebox.askyesno(
                "Confirm undo",
                "The latest organization operation "
                "will be reversed.\n\nContinue?",
            )

            if not confirmed:
                return

        self.run_background(
            operation=lambda: self.undo_operation(
                dry_run
            ),
            status="Restoring files...",
        )

    def undo_operation(
        self,
        dry_run: bool,
    ) -> None:
        """Undo the latest file organization."""

        if dry_run:
            logging.warning(
                "DRY RUN is enabled. "
                "Files will not be restored."
            )

        undo_last_operation(
            dry_run=dry_run
        )

    def clear_log(self) -> None:
        """Clear the GUI activity log."""

        self.log_text.configure(
            state="normal"
        )
        self.log_text.delete(
            "1.0",
            tk.END,
        )
        self.log_text.configure(
            state="disabled"
        )


def main() -> None:
    """Start the graphical application."""

    root = tk.Tk()
    FileOrganizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()