from pathlib import Path

from loguru import logger

if __name__ == "__main__":
    from single_py_file_handler import PyFileNotesRemover
else:
    from src.utils.single_py_file_handler import PyFileNotesRemover


class RemoveFilesNotes:
    """
    Remove notes from all.py files in a folder
    """

    def __init__(self, folder_path: Path):
        self.folder_path = folder_path
        self.__remove_notes()

    def __remove_notes(self):
        for py_file_path in Path(self.folder_path).rglob("*.py"):
            logger.info(f"Removing notes from {py_file_path}...")
            PyFileNotesRemover(py_file_path)


if __name__ == "__main__":

    def test():
        print("Test remove notes from .py files in ./tests/examples folder")
        folder_path = Path("tests\examples")
        RemoveFilesNotes(folder_path)

    test()
