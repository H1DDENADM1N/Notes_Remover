import ast
import json
import shutil
import tokenize
from abc import ABC, abstractmethod
from io import StringIO
from pathlib import Path
from typing import Dict, List, Set, Tuple

from loguru import logger


class BasePyFileProcessor(ABC):
    """
    Python文件处理器基类
    提供通用的文件分析和注释处理功能
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_content: str = ""
        self.lines: List[str] = []
        self.tokens: List[tokenize.TokenInfo] = []

        self._read_file()
        self._tokenize_file()

    def _read_file(self) -> None:
        """读取文件内容"""
        try:
            self.file_content = self.file_path.read_text(encoding="utf-8")
            self.lines = self.file_content.splitlines()
        except (FileNotFoundError, UnicodeDecodeError) as e:
            logger.error(f"读取文件时出错 {self.file_path}: {e}")

    def _tokenize_file(self) -> None:
        """对文件进行词法分析"""
        try:
            self.tokens = list(
                tokenize.generate_tokens(StringIO(self.file_content).readline)
            )
        except tokenize.TokenError as e:
            logger.warning(f"词法分析遇到问题: {e}")
            self.tokens = []

    def _is_standalone_string(self, string_token_index: int) -> bool:
        """检查字符串是否是独立的（不是赋值或函数调用的一部分）"""
        if not self.tokens or string_token_index >= len(self.tokens):
            return True

        # 获取前一个非空token
        prev_index = string_token_index - 1
        while prev_index >= 0 and self.tokens[prev_index].type in (
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.INDENT,
        ):
            prev_index -= 1

        if prev_index < 0:
            return True

        prev_token = self.tokens[prev_index]

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
        while next_index < len(self.tokens) and self.tokens[next_index].type in (
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.DEDENT,
        ):
            next_index += 1

        if next_index < len(self.tokens):
            next_token = self.tokens[next_index]
            if next_token.type == tokenize.OP and next_token.string in (
                ")",
                "]",
                "}",
                ",",
            ):
                return False

        return True

    def _find_triple_quotes(self, line: str, start_pos: int = 0) -> int:
        """查找三引号的位置"""
        for i in range(start_pos, len(line) - 2):
            if line[i : i + 3] in ('"""', "'''"):
                return i
        return -1

    def _get_standalone_strings(self) -> List[Tuple[int, int, str]]:
        """获取所有独立字符串"""
        standalone_strings = []
        processed_lines = set()

        for i, token in enumerate(self.tokens):
            if token.type == tokenize.STRING:
                string_value = token.string
                start_line = token.start[0]

                if start_line in processed_lines:
                    continue

                # 检查是否是三引号字符串
                is_triple_quoted = (
                    string_value.startswith('"""') or string_value.startswith("'''")
                ) and len(string_value) >= 6

                if is_triple_quoted and self._is_standalone_string(i):
                    end_line = token.end[0] if token.end[0] > start_line else start_line

                    for line_num in range(start_line, end_line + 1):
                        processed_lines.add(line_num)

                    standalone_strings.append((start_line, end_line, string_value))

        return standalone_strings

    def _get_docstring_lines(self) -> Set[int]:
        """使用AST识别文档字符串的行号"""
        docstring_lines = set()

        try:
            tree = ast.parse(self.file_content)

            class DocstringVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.docstring_lines = set()

                def visit_Module(self, node):
                    self._process_docstring_node(node)
                    self.generic_visit(node)

                def visit_ClassDef(self, node):
                    self._process_docstring_node(node)
                    self.generic_visit(node)

                def visit_FunctionDef(self, node):
                    self._process_docstring_node(node)
                    self.generic_visit(node)

                def _process_docstring_node(self, node):
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Str)
                    ):
                        start_line = node.body[0].lineno
                        end_line = getattr(node.body[0], "end_lineno", start_line)
                        for line in range(start_line, end_line + 1):
                            self.docstring_lines.add(line)

            visitor = DocstringVisitor()
            visitor.visit(tree)
            docstring_lines = visitor.docstring_lines

        except SyntaxError as e:
            logger.warning(f"AST解析失败: {e}")

        return docstring_lines

    @abstractmethod
    def process(self):
        """处理文件的主要逻辑"""
        pass


class PyFileNotesAnalyzer(BasePyFileProcessor):
    """
    分析统计单个.py文件中的注释
    """

    def __init__(self, file_path: Path):
        self.notes_dict: Dict[int, str] = {}
        self.notes_line_number: int = 0
        self.total_line_number: int = 0
        self.notes_line_percentage: float = 0.0
        self.notes_letter_number: int = 0
        self.total_letter_number: int = 0
        self.notes_letter_percentage: float = 0.0

        super().__init__(file_path)
        self.process()

    def process(self):
        """分析文件注释"""
        if self.tokens:
            self._analyze_with_tokenize()
        else:
            self._fallback_analysis()

        self._calculate_statistics()

    def _analyze_with_tokenize(self):
        """使用tokenize分析注释"""
        # 处理单行注释
        for token in self.tokens:
            if token.type == tokenize.COMMENT and token.string.strip():
                self.notes_dict[token.start[0]] = token.string

        # 处理独立字符串
        for start_line, end_line, content in self._get_standalone_strings():
            lines = content.split("\n")
            for i, line in enumerate(lines):
                line_num = start_line + i
                self.notes_dict[line_num] = line

    def _fallback_analysis(self):
        """备用分析方法"""
        logger.info("使用备用注释分析方法")

        i = 0
        while i < len(self.lines):
            line = self.lines[i].rstrip()

            # 处理单行注释
            if "#" in line:
                comment_start = line.find("#")
                quotes_before = line[:comment_start].count('"') + line[
                    :comment_start
                ].count("'")
                if quotes_before % 2 == 0:  # 不在字符串中
                    comment_content = line[comment_start:]
                    if comment_content.strip():
                        self.notes_dict[i + 1] = comment_content

            # 处理多行字符串
            triple_quotes_pos = self._find_triple_quotes(line)
            if triple_quotes_pos >= 0 and self._is_standalone_string_simple(i):
                j = i
                while j < len(self.lines):
                    current_line = self.lines[j]
                    self.notes_dict[j + 1] = current_line.rstrip()

                    end_quotes = self._find_triple_quotes(
                        current_line, triple_quotes_pos + 3 if j == i else 0
                    )
                    if end_quotes >= 0 and j > i:
                        break
                    j += 1
                i = j

            i += 1

    def _is_standalone_string_simple(self, line_index: int) -> bool:
        """简单检查字符串是否是独立的"""
        if line_index == 0:
            return True

        prev_line = self.lines[line_index - 1].strip()
        if not prev_line:
            return True

        # 如果前一行以这些结尾，可能不是独立字符串
        if prev_line.endswith(("=", "(", "[", "{", ",")):
            return False

        return True

    def _calculate_statistics(self):
        """计算统计信息"""
        self.notes_line_number = len(self.notes_dict)
        self.total_line_number = len(self.lines) + 1  # EOF也算一行
        self.notes_letter_number = sum(
            len(content) for content in self.notes_dict.values()
        )
        self.total_letter_number = len(self.file_content)

        if self.total_line_number > 1:
            self.notes_line_percentage = (
                self.notes_line_number / self.total_line_number
            ) * 100
        if self.total_letter_number > 0:
            self.notes_letter_percentage = (
                self.notes_letter_number / self.total_letter_number
            ) * 100

    def print_details(self) -> None:
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

    def get_details_json(self) -> str:
        """获取注释信息并以JSON格式返回"""
        details = {
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
        return json.dumps(details, ensure_ascii=False, indent=4)


class PyFileNotesRemover(BasePyFileProcessor):
    """
    移除单个.py文件中的注释
    """

    def __init__(self, file_path: Path):
        self.lines_to_remove: Set[int] = set()
        super().__init__(file_path)
        self._create_backup()
        self.process()

    def _create_backup(self) -> None:
        """创建文件备份"""
        if self.file_path.exists():
            backup_path = self.file_path.with_suffix(".py.bak")
            try:
                shutil.copy(str(self.file_path), str(backup_path))
                logger.success(f"备份已创建: {backup_path}")
            except Exception as e:
                logger.error(f"创建备份时出错: {e}")
        else:
            logger.error(f"错误: 文件 '{self.file_path}' 不存在")

    def process(self):
        """移除注释"""
        if self.tokens:
            self._remove_with_tokenize()
        else:
            self._fallback_removal()

        self._write_modified_file()

    def _remove_with_tokenize(self):
        """使用tokenize移除注释"""
        docstring_lines = self._get_docstring_lines()

        # 处理单行注释
        for token in self.tokens:
            if token.type == tokenize.COMMENT:
                self.lines_to_remove.add(token.start[0])
                logger.debug(f"标记单行注释: 行 {token.start[0]}")

        # 处理文档字符串
        for line in docstring_lines:
            self.lines_to_remove.add(line)
            logger.debug(f"标记文档字符串: 行 {line}")

        # 处理独立的多行字符串注释
        for start_line, end_line, content in self._get_standalone_strings():
            # 跳过已经是文档字符串的行
            if any(line in docstring_lines for line in range(start_line, end_line + 1)):
                continue

            for line_num in range(start_line, end_line + 1):
                self.lines_to_remove.add(line_num)
                logger.debug(f"标记独立字符串: 行 {line_num}")

    def _fallback_removal(self):
        """备用移除方法"""
        logger.info("使用备用注释移除方法")

        docstring_lines = self._get_docstring_lines()

        for i, line in enumerate(self.lines):
            line_num = i + 1

            # 跳过文档字符串
            if line_num in docstring_lines:
                self.lines_to_remove.add(line_num)
                continue

            # 处理单行注释
            if "#" in line:
                comment_start = line.find("#")
                # 检查是否在字符串中
                quotes_before = line[:comment_start].count('"') + line[
                    :comment_start
                ].count("'")
                if quotes_before % 2 == 0:  # 不在字符串中
                    self.lines_to_remove.add(line_num)

            # 处理独立的多行字符串
            triple_quotes_pos = self._find_triple_quotes(line)
            if (
                triple_quotes_pos >= 0
                and self._is_standalone_string_simple(i)
                and line_num not in docstring_lines
            ):
                # 检查是否真的是注释（以三引号开头且前面只有空格）
                if line[:triple_quotes_pos].strip() == "":
                    j = i
                    while j < len(self.lines):
                        current_line = self.lines[j]
                        end_quotes = self._find_triple_quotes(
                            current_line, triple_quotes_pos + 3 if j == i else 0
                        )
                        self.lines_to_remove.add(j + 1)
                        if end_quotes >= 0 and j > i:
                            break
                        j += 1
                    i = j

    def _is_standalone_string_simple(self, line_index: int) -> bool:
        """简单检查字符串是否是独立的"""
        if line_index == 0:
            return True

        line = self.lines[line_index].strip()
        prev_line = self.lines[line_index - 1].strip()

        # 如果当前行以三引号开头且前面只有空格，并且前一行是空的或以特定字符结尾
        if (line.startswith('"""') or line.startswith("'''")) and not prev_line:
            return True

        # 如果前一行以这些结尾，可能不是独立字符串
        if prev_line.endswith(("=", "(", "[", "{", ",", ":")):
            return False

        return True

    def _write_modified_file(self):
        """写入修改后的文件"""
        new_lines = []
        for i, line in enumerate(self.lines):
            line_num = i + 1
            if line_num not in self.lines_to_remove:
                new_lines.append(line)
            else:
                # 对于包含代码和注释的行，只移除注释部分
                if "#" in line and line.strip() and not line.strip().startswith("#"):
                    comment_start = line.find("#")
                    # 检查#是否在字符串中
                    quotes_before = line[:comment_start].count('"') + line[
                        :comment_start
                    ].count("'")
                    if quotes_before % 2 == 0:  # 不在字符串中
                        new_lines.append(line[:comment_start].rstrip())
                    else:
                        new_lines.append(line)
                else:
                    # 对于纯注释行，保留空行以维持结构
                    new_lines.append("")

        new_content = "\n".join(new_lines)
        self.file_path.write_text(new_content, encoding="utf-8")
        # 补回 EOF 行
        # 追加空行
        with self.file_path.open("a", encoding="utf-8") as f:
            f.write("\n")

        removed_count = len(self.lines_to_remove)
        total_count = len(self.lines) + 1  # EOF也算一行
        logger.info(f"移除了 {removed_count} 行注释，共 {total_count} 行代码")


if __name__ == "__main__":

    def test_analyzer():
        """测试分析器"""
        print("测试 example.py 文件的注释信息")
        py_file_path = Path("tests/examples/example.py")
        result = PyFileNotesAnalyzer(py_file_path)
        result.print_details()

        json_output = result.get_details_json()
        print("JSON输出:")
        print(json_output)

    def test_remover():
        """测试移除器"""
        print("测试移除 tests/examples/example.py 文件的注释")
        py_file_path = Path("tests/examples/example.py")
        PyFileNotesRemover(py_file_path)

    test_analyzer()
    test_remover()
