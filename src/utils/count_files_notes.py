import json
from pathlib import Path

if __name__ == "__main__":
    from single_py_file_handler import PyFileNotesAnalyzer
else:
    from src.utils.single_py_file_handler import PyFileNotesAnalyzer


class CountFilesNotes:
    """
    Counts the comments of all .py files in the specified folder.

    parameters:
        folder_path: str,

    attributes:
        py_files_list: list[Path], A list of all .py files in the specified folder.
        result_dict: dict, Dictionary storing comment information for each .py file
            key is the path to the file.
            value is the comment information in JSON format.

    methods:
        print_notes_details(self) -> None: Prints the comment information for each .py file

    """

    def __init__(self, folder_path: Path):
        self.folder_path = folder_path
        self.py_files_list = self.__generate_py_files_list()
        self.result_dict = {}
        self.__analyze_each_py_file()

    def __generate_py_files_list(self) -> list:
        py_files_list: list[Path] = []
        for py_file_path in Path(self.folder_path).rglob("*.py"):
            py_files_list.append(py_file_path)
        return py_files_list

    def __analyze_each_py_file(self) -> None:
        for py_file_path in self.py_files_list:
            count_single_file = PyFileNotesAnalyzer(py_file_path)
            # Get comment details in JSON format
            json_notes_details = count_single_file.get_details_json()
            # Store the JSON string in the results dictionary
            # key is the path to the file.
            # value is the comment information in JSON format.
            self.result_dict[py_file_path] = json_notes_details

    def print_notes_details(self) -> None:
        for k, v in self.result_dict.items():
            print("=" * 80)
            print(f"文件名：{k.name}")
            # logger.debug(f"\nJSON Format Value：\n{v}\n")
            print("注释信息：")
            print("-" * 80)
            print("行号\t注释内容")
            notes_details = json.loads(v)
            for note_entry in notes_details["注释信息"]:
                line_number = note_entry["行号"]
                note_content = repr(note_entry["内容"].replace("\\n", "\n")).strip("'")
                print(f"{line_number}\t{note_content}")
            print("-" * 80)
            print(
                f"注释行数：\t{notes_details['注释行数']}\t\t总行数：\t{notes_details['总行数']}\t\t注释占比：\t{notes_details['注释占比']:.0f}%"
            )
            print(
                f"注释字母数：\t{notes_details['注释字母数']}\t\t总字母数：\t{notes_details['总字母数']}\t\t注释字母占比：\t{notes_details['注释字母占比']:.0f}%"
            )
        print("=" * 80)


if __name__ == "__main__":

    def test():
        folder_path = Path("tests\examples")
        result = CountFilesNotes(folder_path)
        result.print_notes_details()

    print("Test print all .py files notes in ./tests/examples folder")
    test()
