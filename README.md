# Smart Downloads Organizer

Smart Downloads Organizer is a Python automation application that helps users organize files, detect duplicate files, and safely undo file movements.

The project includes both a graphical interface built with Tkinter and a command-line interface.

## Features

- Organizes files into folders based on their extensions
- Supports custom categories through `config.json`
- Includes a safe dry-run mode
- Detects duplicate files using SHA-256 hashes
- Generates a CSV report of duplicate files
- Protects existing files from being overwritten
- Stores file movement history
- Can undo the latest organization operation
- Records activity in a log file
- Includes a graphical user interface
- Can be converted into a Windows executable

## Project Structure

```text
SmartDownloadsOrganizer/
├── main.py
├── gui.py
├── organizer.py
├── duplicates.py
├── history.py
├── config.py
├── config.json
├── README.md
└── .gitignore
```

### File descriptions

- `main.py` — command-line interface
- `gui.py` — graphical interface
- `organizer.py` — file sorting logic
- `duplicates.py` — duplicate file detection
- `history.py` — movement history and undo functionality
- `config.py` — application configuration loader
- `config.json` — editable file categories

## Requirements

- Python 3.10 or newer
- Tkinter
- Windows, macOS, or Linux

Tkinter is included with most standard Python installations.

## Installation

Clone the repository:

```bash
git clone https://github.com/trumanch/smart-downloads-organizer.git
cd smart-downloads-organizer
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

## Graphical Interface

Start the graphical application:

```bash
python gui.py
```

The graphical interface allows users to:

- select a folder;
- preview planned file movements;
- organize files;
- search for duplicate files;
- generate a duplicate report;
- undo the latest organization operation;
- view application activity.

For safety, dry-run mode is enabled by default in the graphical interface.

## Command-Line Interface

Show all available commands:

```bash
python main.py --help
```

### Preview file organization

This command shows what the program would do without moving files:

```bash
python main.py --folder "C:\Path\To\Folder" --dry-run
```

### Organize files

```bash
python main.py --folder "C:\Path\To\Folder"
```

When no folder is provided, the application uses the current user's Downloads folder.

### Find duplicate files

```bash
python main.py --folder "C:\Path\To\Folder" --find-duplicates
```

Duplicate detection works in two stages:

1. Files are grouped by size.
2. Files with the same size are compared using SHA-256 hashes.

The application does not automatically delete duplicate files.

When duplicates are found, the program creates:

```text
duplicates_report.csv
```

### Preview undo

```bash
python main.py --undo --dry-run
```

### Undo the latest organization

```bash
python main.py --undo
```

The application stores file movement information in:

```text
move_history.json
```

If the original file location is already occupied, the restored file receives a safe alternative name instead of overwriting the existing file.

## Custom File Categories

File categories are stored in `config.json`.

Example:

```json
{
    "categories": {
        "Images": [
            ".jpg",
            ".jpeg",
            ".png"
        ],
        "Documents": [
            ".pdf",
            ".docx",
            ".txt"
        ],
        "Design": [
            ".psd",
            ".ai",
            ".fig"
        ]
    }
}
```

Extensions can be written with or without a dot. The application automatically normalizes them.

Restart the application after editing `config.json`.

Files with unknown extensions are moved into the `Other` category.

## Build a Windows Executable

Install PyInstaller:

```bash
python -m pip install pyinstaller
```

Build the application:

```bash
python -m PyInstaller --noconfirm --clean --onefile --windowed --name SmartDownloadsOrganizer gui.py
```

The executable will be created in:

```text
dist/SmartDownloadsOrganizer.exe
```

Copy `config.json` into the `dist` folder so categories can still be edited:

```powershell
Copy-Item .\config.json .\dist\config.json
```

The final application folder should contain:

```text
dist/
├── SmartDownloadsOrganizer.exe
└── config.json
```

## Generated Files

The application may generate the following files:

```text
organizer.log
duplicates_report.csv
move_history.json
```

These files are excluded from Git through `.gitignore`.

## Safety

- Duplicate files are never deleted automatically.
- Existing files are never overwritten.
- Dry-run mode previews operations before files are moved.
- The latest organization operation can be undone.
- Important folders should always be tested with dry-run mode first.

## Technologies

- Python
- Tkinter
- pathlib
- argparse
- hashlib
- JSON
- CSV
- PyInstaller

## Future Improvements

Possible future improvements include:

- automatic background folder monitoring;
- multiple undo operations;
- duplicate file management inside the graphical interface;
- configurable destination folders;
- file statistics and charts;
- automated tests;
- dark mode support.

## License

This project is intended for educational and portfolio purposes.