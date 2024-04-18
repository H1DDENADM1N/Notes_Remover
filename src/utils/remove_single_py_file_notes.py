import json
import re
import shutil
from pathlib import Path

from loguru import logger


class RemoveSinglePyFileNotes:
    """
    Removing comments from a single .py file

    parameters:
        file_path: Path, Path to the file from which you want to delete the comment

    """

    def __init__(self, file_path: Path):
        self.file_content: str = ""
        self.file_path = file_path
        self.__create_backup(file_path)
        self.__analyze_file(file_path)

    def __create_backup(self, file_path: Path) -> None:
        """
        Create a backup of the file before modifying it
        """
        # Ensure the file exists before attempting to create a backup
        if file_path.exists():
            # Create a backup file path by adding .bak before the existing suffix
            backup_file_path = file_path.with_suffix(".py.bak")
            try:
                # Copy the file to the backup file path
                shutil.copy(str(file_path), str(backup_file_path))
                logger.success(f"Backup created: {backup_file_path}")
            except FileNotFoundError as e:
                logger.error(f"Error: The file '{file_path}' does not exist.")
            except PermissionError as e:
                logger.error(
                    f"Error: Permission denied when trying to access '{file_path}'."
                )
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
        else:
            logger.error(f"Error: The file '{file_path}' does not exist.")

    def __analyze_file(self, file_path: Path) -> None:
        """
        Analyze the contents of the file and remove comments
        """
        try:
            self.file_content = file_path.read_text()
            # Analyzing single-line comments
            self.__analyze_single_line_note()
            # Analyzing multi-line comments
            self.__analyze_multi_line_comment()
            # Write the modified file
            Path.write_text(self.file_path, self.file_content)
            logger.success(f"Modified file: {file_path}")
        except (IndexError, FileNotFoundError) as e:
            logger.error(f"Error: {e}\nfile_path: {file_path}")

    def __analyze_single_line_note(self) -> None:
        """
        Analyzing single-line comments
        (lines starting with '#' and lines included '#')
        """
        for line in self.file_content.split("\n"):
            if line.startswith("#"):
                self.__remove_single_line_note(
                    line[1:]
                )  # Strip from the second character
            elif "#" in line:
                index = line.index("#")
                self.__remove_single_line_note(
                    line[index + 1 :]
                )  # Strip from the index after the '#' symbol
            else:
                continue

    def __remove_single_line_note(self, note_content: str) -> None:
        self.file_content = self.file_content.replace(f"#{note_content}\n", "\n")
        logger.info(f"Removed note: #{note_content}")

    def __analyze_multi_line_comment(self) -> None:
        """
        Analyzing multi-line comments
        (wrapped by \"\"\" or \'\'\'\' and not within the body of the function (outer layer not wrapped by parentheses))
        """
        pattern = r'(?s)(?<!\( )((\'{3}|"{3})(.+?)\2)(?!\s*\))'
        matches = re.findall(pattern, self.file_content)
        for match in matches:
            # Match to a multi-line comment and delete the annotation content
            self.__remove_multi_line_comment(match)

    def __remove_multi_line_comment(self, match: re.Match) -> None:
        self.file_content = self.file_content.replace(f"{match[0]}\n", "", 1)
        logger.info(f"Removed multi-line comment: {match[0]}")


def test():
    print("Test to remove . /tests/examples/example2.py file's comments.")
    py_file_path = Path("tests\examples\example2.py")
    RemoveSinglePyFileNotes(py_file_path)


if __name__ == "__main__":
    test()
