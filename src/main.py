import sys
import argparse
from loguru import logger
from pathlib import Path
from src.utils.single_py_file_handler import PyFileNotesAnalyzer, PyFileNotesRemover
from src.utils.count_files_notes import CountFilesNotes
from src.utils.remove_files_notes import RemoveFilesNotes
from src.__init__ import __version__


class ArgsConflictError(Exception):
    """Exception raised when there is a conflict in command line arguments."""

    pass


def parse_arguments():
    """
    Define argparse arguments and options
    """

    parser = argparse.ArgumentParser(
        description="Count or Remove notes from a .py file or a directory of .py files"
    )
    parser.add_argument(
        "PATH", help="Path to the file or directory to count or remove notes from"
    )
    parser.add_argument(
        "-c",
        "--count_notes",
        action="store_true",
        help="Count notes from a .py file or a directory of .py files",
    )
    parser.add_argument(
        "-r",
        "--remove_notes",
        action="store_true",
        help="Remove notes from a .py file or a directory of .py files",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show version",
    )
    return parser.parse_args()


def count_notes(args_path: Path) -> None:
    """
    Counts and prints:
        the number of comment lines
        the content of comments
        the percentage of comment lines
        the number of comment letters
        the total number of letters
        the percentage of comment letters
    Form:
        a single .py file
        or .py files in a directory
    """
    if not args_path.exists():
        raise FileNotFoundError(f"File or directory not found: {args_path}")

    if args_path.is_file() and args_path.suffix == ".py":
        result = PyFileNotesAnalyzer(py_file_path := args_path)
    elif args_path.is_dir():
        result = CountFilesNotes(folder_path := args_path)
    result.print_notes_details()


def remove_notes(args_path: Path) -> None:
    """
    Removes notes from a single .py file or .py files in a directory."""
    if not args_path.exists():
        raise FileNotFoundError(f"File or directory not found: {args_path}")

    if args_path.is_file() and args_path.suffix == ".py":
        PyFileNotesRemover(py_file_path := args_path)
    elif args_path.is_dir():
        RemoveFilesNotes(folder_path := args_path)


def main():
    args = parse_arguments()

    args_path = Path(args.PATH)
    # logger.debug(f"args_path: {args_path}")

    if not args.remove_notes and not args.count_notes:
        count_notes(args_path)
    elif args.remove_notes and not args.count_notes:
        remove_notes(args_path)
    elif not args.remove_notes and args.count_notes:
        count_notes(args_path)
    elif args.remove_notes and args.count_notes:
        raise ArgsConflictError(
            "Should not provide both options -c and -r at the same time."
        )
