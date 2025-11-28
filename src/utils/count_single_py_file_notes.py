import json
import tokenize
from io import StringIO
from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger


class CountSinglePyFileNotes:
    """
    分析统计单个.py文件中的注释

    parameters:
        file_path: 文件路径

    attributes:
        notes_dict: 字典，key为注释所在行数，value为注释内容
        notes_line_number: 注释行数
        total_line_number: 总行数
        notes_line_percentage: 注释行数占比
        notes_letter_number: 注释字母数
        total_letter_number: 总字母数
        notes_letter_percentage: 注释字母占比
    """

    def __init__(self, file_path: Path):
        self.notes_dict: Dict[int, str] = {}
        self.file_content: str = ""
        self.notes_line_number: int = 0
        self.total_line_number: int = 0
        self.notes_line_percentage: float = 0.0
        self.notes_letter_number: int = 0
        self.total_letter_number: int = 0
        self.notes_letter_percentage: float = 0.0

        self.__analyze_file(file_path)
        self.__calculate_notes_line_percentage()
        self.__calculate_notes_letter_percentage()

    def print_notes_details(self) -> None:
        """打印注释信息"""
        print("注释信息：")
        print("-" * 80)
        print("行号\t注释内容")
        for line_num, content in sorted(self.notes_dict.items()):
            print(f"{line_num}\t{repr(content).strip("'")}")
        print("-" * 80)
        print(
            f"注释行数：\t{self.notes_line_number}\t\t总行数：\t{self.total_line_number}\t\t注释占比：\t{self.notes_line_percentage:.0f}%"
        )
        print(
            f"注释字母数：\t{self.notes_letter_number}\t\t总字母数：\t{self.total_letter_number}\t\t注释字母占比：\t{self.notes_letter_percentage:.0f}%\n"
        )

    def get_notes_details(self) -> str:
        """获取注释信息并以JSON格式返回"""
        notes_details = {
            "注释信息": [
                {"行号": line_num, "内容": content.replace("\n", "\\n")}
                for line_num, content in sorted(self.notes_dict.items())
            ],
            "注释行数": self.notes_line_number,
            "总行数": self.total_line_number,
            "注释占比": round(self.notes_line_percentage, 2),
            "注释字母数": self.notes_letter_number,
            "总字母数": self.total_letter_number,
            "注释字母占比": round(self.notes_letter_percentage, 2),
        }

        return json.dumps(notes_details, ensure_ascii=False, indent=4)

    def __calculate_notes_line_percentage(self) -> None:
        """计算注释行数占比"""
        self.notes_line_number = len(self.notes_dict)
        self.total_line_number = len(self.file_content.splitlines())
        if self.total_line_number > 0:
            self.notes_line_percentage = (
                self.notes_line_number / self.total_line_number
            ) * 100

    def __calculate_notes_letter_percentage(self) -> None:
        """计算注释字母数占比"""
        self.notes_letter_number = sum(
            len(content) for content in self.notes_dict.values()
        )
        self.total_letter_number = len(self.file_content)
        if self.total_letter_number > 0:
            self.notes_letter_percentage = (
                self.notes_letter_number / self.total_letter_number
            ) * 100

    def __analyze_file(self, file_path: Path) -> None:
        """分析文件内容"""
        try:
            self.file_content = file_path.read_text(encoding="utf-8")
            self.__analyze_comments_with_tokenize()
        except (FileNotFoundError, UnicodeDecodeError, SyntaxError) as e:
            logger.error(f"分析文件时出错 {file_path}: {e}")

    def __analyze_comments_with_tokenize(self) -> None:
        """使用tokenize模块进行词法分析"""
        try:
            # 将文件内容转换为token流
            tokens = list(
                tokenize.generate_tokens(StringIO(self.file_content).readline)
            )

            # 处理单行注释（包含#号）
            for token in tokens:
                if token.type == tokenize.COMMENT:
                    self.__process_comment_token_with_hash(token)

            # 处理文档字符串和独立字符串
            self.__process_docstrings_and_strings(tokens)

        except tokenize.TokenError as e:
            logger.warning(f"词法分析遇到问题: {e}，使用简单分析")
            self.__fallback_analysis_with_quotes()

    def __process_comment_token_with_hash(self, token: tokenize.TokenInfo) -> None:
        """处理注释token，包含#号"""
        comment_content = token.string
        if comment_content.strip():  # 只记录非空注释
            self.notes_dict[token.start[0]] = comment_content

    def __process_docstrings_and_strings(
        self, tokens: List[tokenize.TokenInfo]
    ) -> None:
        """处理文档字符串和独立字符串"""
        # 首先识别所有独立的字符串（可能是文档字符串）
        standalone_strings = self.__identify_standalone_strings(tokens)

        # 处理这些独立字符串
        for start_line, end_line, content in standalone_strings:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                line_num = start_line + i
                self.notes_dict[line_num] = line

    def __identify_standalone_strings(
        self, tokens: List[tokenize.TokenInfo]
    ) -> List[Tuple[int, int, str]]:
        """识别独立的字符串（可能是文档字符串）"""
        standalone_strings = []
        processed_lines = set()

        for i, token in enumerate(tokens):
            if token.type == tokenize.STRING:
                string_value = token.string
                start_line = token.start[0]

                # 如果这个字符串已经被处理过，跳过
                if start_line in processed_lines:
                    continue

                # 检查是否是三引号字符串
                is_triple_quoted = (
                    string_value.startswith('"""') or string_value.startswith("'''")
                ) and len(string_value) >= 6

                if is_triple_quoted:
                    # 检查是否是独立的字符串
                    if self.__is_standalone_string(tokens, i):
                        # 计算结束行
                        end_line = (
                            token.end[0] if token.end[0] > start_line else start_line
                        )

                        # 标记已处理的行
                        for line_num in range(start_line, end_line + 1):
                            processed_lines.add(line_num)

                        # 记录字符串内容
                        standalone_strings.append((start_line, end_line, string_value))

        return standalone_strings

    def __is_standalone_string(
        self, tokens: List[tokenize.TokenInfo], string_token_index: int
    ) -> bool:
        """检查字符串是否是独立的（不是赋值或函数调用的一部分）"""
        # 获取前一个非空token
        prev_index = string_token_index - 1
        while prev_index >= 0 and tokens[prev_index].type in (
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.INDENT,
        ):
            prev_index -= 1

        if prev_index < 0:
            # 字符串在文件开头，可能是模块文档字符串
            return True

        prev_token = tokens[prev_index]

        # 如果前一个token是这些，说明字符串是表达式的一部分
        if prev_token.type == tokenize.OP and prev_token.string in (
            "(",
            "[",
            "{",
            ",",
            "=",
        ):
            return False
        if prev_token.type == tokenize.NAME and prev_token.string in (
            "def",
            "class",
            "return",
        ):
            return False

        # 获取后一个非空token
        next_index = string_token_index + 1
        while next_index < len(tokens) and tokens[next_index].type in (
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.DEDENT,
        ):
            next_index += 1

        if next_index < len(tokens):
            next_token = tokens[next_index]
            # 如果后一个token是这些，说明字符串是表达式的一部分
            if next_token.type == tokenize.OP and next_token.string in (
                ")",
                "]",
                "}",
                ",",
            ):
                return False

        return True

    def __fallback_analysis_with_quotes(self) -> None:
        """备用分析方法（当tokenize失败时使用），包含引号"""
        logger.info("使用备用注释分析方法")
        lines = self.file_content.splitlines()

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            # 处理单行注释（包含#号）
            if "#" in line:
                comment_start = line.find("#")
                # 简单检查#是否在字符串中（检查前面的引号数量）
                quotes_before = line[:comment_start].count('"') + line[
                    :comment_start
                ].count("'")
                if quotes_before % 2 == 0:  # 不在字符串中
                    # 记录从#开始到行尾的所有内容
                    comment_content = line[comment_start:]
                    if comment_content.strip():
                        self.notes_dict[i + 1] = comment_content

            # 处理多行字符串注释
            triple_quotes_pos = self.__find_triple_quotes(line)
            if triple_quotes_pos >= 0:
                # 检查是否是独立的字符串
                if self.__is_standalone_string_simple(lines, i, triple_quotes_pos):
                    # 记录多行字符串
                    j = i
                    while j < len(lines):
                        current_line = lines[j]
                        self.notes_dict[j + 1] = current_line.rstrip()

                        # 检查是否结束
                        end_quotes = self.__find_triple_quotes(
                            current_line, triple_quotes_pos + 3 if j == i else 0
                        )
                        if end_quotes >= 0 and j > i:
                            break
                        j += 1
                    i = j  # 跳过已处理的行

            i += 1

    def __find_triple_quotes(self, line: str, start_pos: int = 0) -> int:
        """查找三引号的位置"""
        for i in range(start_pos, len(line) - 2):
            if line[i : i + 3] in ('"""', "'''"):
                return i
        return -1

    def __is_standalone_string_simple(
        self, lines: List[str], line_index: int, quote_pos: int
    ) -> bool:
        """简单检查字符串是否是独立的"""
        if line_index == 0:
            return True

        prev_line = lines[line_index - 1].rstrip()
        if not prev_line:
            return True

        # 如果前一行以这些结尾，可能不是独立字符串
        if prev_line.endswith(("=", "(", "[", "{", ",")):
            return False

        return True


def test():
    """测试函数"""
    print("测试 example.py 文件的注释信息")
    py_file_path = Path("tests/examples/example.py")
    result = CountSinglePyFileNotes(py_file_path)
    result.print_notes_details()

    # 输出JSON格式
    json_output = result.get_notes_details()
    print("JSON输出:")
    print(json_output)


if __name__ == "__main__":
    test()
