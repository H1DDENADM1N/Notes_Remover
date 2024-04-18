import json
import re
from pathlib import Path

from loguru import logger


class CountSinglePyFileNotes:
    """
    统计单个 .py文件 中注释的行数和内容，并计算注释行数占比和注释字母数占比

    parameters:
        file_path: 文件路径

    attributes:
        notes_dict: 字典，key 为注释所在行数，value 为注释内容
        notes_line_number: 注释行数
        total_line_number: 总行数
        notes_line_percentage: 注释行数占比

        notes_letter_number: 注释字母数
        total_letter_number: 总字母数
        notes_letter_percentage: 注释字母占比

    methods:
        print_notes_details: 打印注释信息
        get_notes_details: 获取注释信息，以JSON 格式返回

    """

    def __init__(self, file_path: Path):
        self.notes_dict: dict = dict()
        self.file_content: str = ""
        self.notes_line_number: int = 0
        self.total_line_number: int = 0
        self.notes_line_percentage: float = 0.0
        self.notes_letter_number: int = 0
        self.total_letter_number: int = 0
        self.notes_letter_percentage: float = 0.0
        self.__analyze_file(file_path)
        self.__fix_note_dict()
        self.__calculate_notes_line_percentage()
        self.__calculate_notes_letter_percentage()

    def print_notes_details(self) -> None:
        """
        打印注释信息
        """
        print("注释信息：")
        print("-" * 80)
        print("行号\t注释内容")
        for k, v in self.notes_dict.items():
            print(k, "\t", repr(v).strip("'"))
        print("-" * 80)
        print(
            f"注释行数：\t{self.notes_line_number}\t\t总行数：\t{self.total_line_number}\t\t注释占比：\t{self.notes_line_percentage:.0f}%"
        )
        print(
            f"注释字母数：\t{self.notes_letter_number}\t\t总字母数：\t{self.total_letter_number}\t\t注释字母占比：\t{self.notes_letter_percentage:.0f}%\n"
        )

    def get_notes_details(self) -> str:
        """
        获取注释信息并以 JSON 格式返回
        """
        notes_details = {
            "注释信息": [],
            "注释行数": self.notes_line_number,
            "总行数": self.total_line_number,
            "注释占比": self.notes_line_percentage,
            "注释字母数": self.notes_letter_number,
            "总字母数": self.total_letter_number,
            "注释字母占比": self.notes_letter_percentage,
        }

        for k, v in self.notes_dict.items():
            # 将注释内容转换为 JSON 字符串时，确保换行符被转义
            notes_details["注释信息"].append(
                {"行号": k, "内容": v.replace("\n", "\\n")}
            )
            # logger.debug(f"行号：{k}，注释内容：{v}")

        # 将字典转换为 JSON 字符串
        # logger.debug(f"notes_details: {notes_details}")
        return json.dumps(notes_details, ensure_ascii=False, indent=4)

    def __calculate_notes_line_percentage(self) -> None:
        """
        计算注释行数占比
        """
        self.notes_line_number = len(self.notes_dict)
        self.total_line_number = len(self.file_content.split("\n"))
        if self.total_line_number == 0:
            self.notes_line_percentage = 0.0
        else:
            self.notes_line_percentage = (
                self.notes_line_number / self.total_line_number
            ) * 100

    def __calculate_notes_letter_percentage(self) -> None:
        """
        计算注释字母数占比
        """
        notes_set = set()
        for v in self.notes_dict.values():
            notes_set.add(v)
        self.notes_letter_number = sum(len(v) for v in notes_set)
        self.total_letter_number = len(self.file_content)
        if self.total_letter_number == 0:
            self.notes_letter_percentage = 0.0
        else:
            self.notes_letter_percentage = (
                self.notes_letter_number / self.total_letter_number
            ) * 100

    def __add_note(self, line_number: int, note_content: str) -> None:
        self.notes_dict[line_number] = note_content

    def __fix_note_dict(self) -> None:
        """
        修正 notes_dict，尝试去除多行注释间的正常代码行，不完美，但能解决大部分情况
        """
        for k, v in list(self.notes_dict.items()):
            if '"""' in v or "'''" in v:
                self.notes_dict.pop(k)
            elif v.startswith(","):
                self.notes_dict.pop(k)
            elif "+" in v and v.endswith("= "):
                self.notes_dict.pop(k)

    def __analyze_file(self, file_path: Path) -> None:
        """
        分析文件内容，构造 notes_dict
        """
        try:
            self.file_content = file_path.read_text()
            # 分析单行注释
            self.__analyze_single_line_note()
            # 分析多行注释
            self.__analyze_multi_line_comment()
        except (IndexError, FileNotFoundError) as e:
            print(f"Error: {e}\nfile_path: {file_path}")

    def __analyze_single_line_note(self) -> None:
        """
        分析单行注释
        （以 '#' 开头的行 和 行中有 '#' 且 '#' 后面有内容）
        """
        for i, line in enumerate(self.file_content.split("\n")):
            if line.startswith("#"):
                # logger.debug(f"单行注释：{line}")
                self.__add_note(i + 1, line[1:])  # 从第二个字符开始截取
            elif "#" in line:
                # logger.debug(f"行中有 '#' 且 '#' 后面有内容：{line}")
                index = line.index("#")
                self.__add_note(i + 1, line[index + 1 :])  # 从 '#' 符号后面开始截取
            else:
                continue

    def __analyze_multi_line_comment(self) -> None:
        """
        分析多行注释
        （被\"\"\" 或 \'\'\' 包裹，且不在函数体内（外层没有被括号包裹））
        """
        pattern = r'(?s)(?<!\( )((\'{3}|"{3})(.+?)\2)(?!\s*\))'
        matches = re.findall(pattern, self.file_content)
        for match in matches:
            start_line = (
                self.file_content.count("\n", 0, self.file_content.find(match[0])) + 1
            )
            end_line = start_line + match[0].count("\n")
            note_content = match[2]
            # logger.debug(f"多行注释：{note_content}")
            for i in range(start_line, end_line + 1):
                self.__add_note(i, note_content)


def test():
    print("Test Print . /tests/examples/example.py file comment information")
    py_file_path = Path("tests\examples\example.py")
    result = CountSinglePyFileNotes(py_file_path)
    result.print_notes_details()


if __name__ == "__main__":
    test()
