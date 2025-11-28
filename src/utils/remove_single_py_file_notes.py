import ast
import shutil
import tokenize
from io import StringIO
from pathlib import Path
from typing import List, Set, Tuple

from loguru import logger


class RemoveSinglePyFileNotes:
    """
    移除单个.py文件中的注释

    parameters:
        file_path: Path, 要移除注释的文件路径
    """

    def __init__(self, file_path: Path):
        self.file_content: str = ""
        self.file_path = file_path
        self.lines: List[str] = []
        self.lines_to_remove: Set[int] = set()
        self.comment_ranges: List[Tuple[int, int]] = []  # (start_line, end_line)

        self.__create_backup(file_path)
        self.__analyze_file(file_path)

    def __create_backup(self, file_path: Path) -> None:
        """在修改前创建文件备份"""
        if file_path.exists():
            backup_file_path = file_path.with_suffix(".py.bak")
            try:
                shutil.copy(str(file_path), str(backup_file_path))
                logger.success(f"备份已创建: {backup_file_path}")
            except Exception as e:
                logger.error(f"创建备份时出错: {e}")
        else:
            logger.error(f"错误: 文件 '{file_path}' 不存在")

    def __analyze_file(self, file_path: Path) -> None:
        """分析文件内容并移除注释"""
        try:
            self.file_content = file_path.read_text(encoding="utf-8")
            self.lines = self.file_content.splitlines()

            # 使用AST和tokenize分析注释
            self.__analyze_comments_with_ast()

            # 移除注释并写入文件
            self.__remove_comments_and_write()

            logger.success(f"已修改文件: {file_path}")
        except Exception as e:
            logger.error(f"分析文件时出错 {file_path}: {e}")

    def __analyze_comments_with_ast(self) -> None:
        """分析注释"""
        try:
            # 使用AST识别文档字符串
            tree = ast.parse(self.file_content)
            docstring_lines = self.__identify_docstrings_with_ast(tree)

            # 使用tokenize识别所有注释
            self.__analyze_comments_with_tokenize(docstring_lines)

        except SyntaxError as e:
            logger.warning(f"AST解析失败: {e}，使用纯tokenize分析")
            self.__analyze_comments_with_tokenize()

    def __identify_docstrings_with_ast(self, tree: ast.AST) -> Set[int]:
        """识别文档字符串的行号"""
        docstring_lines = set()

        class DocstringVisitor(ast.NodeVisitor):
            def visit_Module(self, node):
                if ast.get_docstring(node):
                    # 模块级文档字符串
                    if node.body and isinstance(node.body[0], ast.Expr):
                        start_line = node.body[0].lineno
                        end_line = (
                            node.body[0].end_lineno
                            if hasattr(node.body[0], "end_lineno")
                            else start_line
                        )
                        for line in range(start_line, end_line + 1):
                            docstring_lines.add(line)

            def visit_ClassDef(self, node):
                if ast.get_docstring(node):
                    # 类文档字符串
                    if node.body and isinstance(node.body[0], ast.Expr):
                        start_line = node.body[0].lineno
                        end_line = (
                            node.body[0].end_lineno
                            if hasattr(node.body[0], "end_lineno")
                            else start_line
                        )
                        for line in range(start_line, end_line + 1):
                            docstring_lines.add(line)

            def visit_FunctionDef(self, node):
                if ast.get_docstring(node):
                    # 函数文档字符串
                    if node.body and isinstance(node.body[0], ast.Expr):
                        start_line = node.body[0].lineno
                        end_line = (
                            node.body[0].end_lineno
                            if hasattr(node.body[0], "end_lineno")
                            else start_line
                        )
                        for line in range(start_line, end_line + 1):
                            docstring_lines.add(line)

        visitor = DocstringVisitor()
        visitor.visit(tree)
        return docstring_lines

    def __analyze_comments_with_tokenize(
        self, docstring_lines: Set[int] = None
    ) -> None:
        """分析注释"""
        if docstring_lines is None:
            docstring_lines = set()

        try:
            tokens = list(
                tokenize.generate_tokens(StringIO(self.file_content).readline)
            )

            # 处理单行注释
            for token in tokens:
                if token.type == tokenize.COMMENT:
                    self.__mark_comment_for_removal(token)

            # 处理文档字符串和独立字符串
            self.__process_docstrings_and_standalone_strings(tokens, docstring_lines)

        except tokenize.TokenError as e:
            logger.warning(f"词法分析遇到问题: {e}，使用简单分析")
            self.__fallback_comment_analysis()

    def __mark_comment_for_removal(self, token: tokenize.TokenInfo) -> None:
        """标记单行注释以便移除"""
        line_num = token.start[0]
        self.lines_to_remove.add(line_num)
        logger.info(f"标记要移除的单行注释 (行 {line_num}): {token.string}")

    def __process_docstrings_and_standalone_strings(
        self, tokens: List[tokenize.TokenInfo], docstring_lines: Set[int]
    ) -> None:
        """处理文档字符串和独立字符串"""
        processed_strings = set()

        for i, token in enumerate(tokens):
            if token.type == tokenize.STRING:
                string_value = token.string
                start_line = token.start[0]

                # 如果这个字符串已经被处理过，跳过
                if start_line in processed_strings:
                    continue

                # 检查是否是三引号字符串
                if (
                    string_value.startswith('"""') or string_value.startswith("'''")
                ) and len(string_value) >= 6:
                    # 检查是否是文档字符串或独立字符串
                    if start_line in docstring_lines or self.__is_standalone_string(
                        tokens, i
                    ):
                        # 计算结束行
                        end_line = (
                            token.end[0] if token.end[0] > start_line else start_line
                        )

                        # 标记要移除的行
                        for line_num in range(start_line, end_line + 1):
                            self.lines_to_remove.add(line_num)
                            processed_strings.add(line_num)

                        logger.info(
                            f"标记要移除的多行注释 (行 {start_line}-{end_line})"
                        )

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

    def __fallback_comment_analysis(self) -> None:
        """备用注释分析方法"""
        logger.info("使用备用注释分析方法")

        in_multiline_string = False
        multiline_start = 0

        for i, line in enumerate(self.lines):
            line_num = i + 1
            stripped_line = line.strip()

            # 处理单行注释
            if "#" in line and not in_multiline_string:
                comment_start = line.find("#")
                # 简单检查#是否在字符串中
                if not self.__is_in_string_simple(line, comment_start):
                    self.lines_to_remove.add(line_num)
                    logger.info(
                        f"标记要移除的单行注释 (行 {line_num}): {line[comment_start:]}"
                    )

            # 检查多行字符串开始
            if not in_multiline_string:
                triple_quotes_pos = self.__find_triple_quotes(line)
                if triple_quotes_pos >= 0 and not self.__is_in_string_simple(
                    line, triple_quotes_pos, True
                ):
                    # 检查是否是独立字符串
                    if self.__is_standalone_string_simple(i):
                        in_multiline_string = True
                        multiline_start = line_num
            else:
                # 在多行字符串中，检查结束
                triple_quotes_pos = self.__find_triple_quotes(line)
                if triple_quotes_pos >= 0:
                    # 标记整个多行字符串要移除
                    for remove_line in range(multiline_start, line_num + 1):
                        self.lines_to_remove.add(remove_line)
                    logger.info(
                        f"标记要移除的多行注释 (行 {multiline_start}-{line_num})"
                    )
                    in_multiline_string = False

    def __is_in_string_simple(
        self, line: str, pos: int, check_triple: bool = False
    ) -> bool:
        """简单检查位置是否在字符串中"""
        quotes_before = line[:pos].count('"') + line[:pos].count("'")
        return quotes_before % 2 == 1

    def __find_triple_quotes(self, line: str) -> int:
        """查找三引号的位置"""
        for i in range(len(line) - 2):
            if line[i : i + 3] in ('"""', "'''"):
                return i
        return -1

    def __is_standalone_string_simple(self, line_index: int) -> bool:
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

    def __remove_comments_and_write(self) -> None:
        """移除标记的注释并写入文件"""
        # 构建不包含注释的新内容
        new_lines = []
        for i, line in enumerate(self.lines):
            line_num = i + 1
            if line_num not in self.lines_to_remove:
                new_lines.append(line)
            else:
                # 对于部分行，可能需要特殊处理（比如行内注释）
                if "#" in line and line.strip() and not line.strip().startswith("#"):
                    # 移除行内注释但保留代码
                    comment_start = line.find("#")
                    if not self.__is_in_string_simple(line, comment_start):
                        new_lines.append(line[:comment_start].rstrip())
                    else:
                        new_lines.append(line)
                else:
                    # 保持空行以维持总行数不变
                    new_lines.append("")

        # 写入文件
        new_content = "\n".join(new_lines)
        self.file_path.write_text(new_content, encoding="utf-8")

        # 记录统计信息
        removed_count = len(self.lines_to_remove)
        total_count = len(self.lines)
        logger.info(f"移除了 {removed_count} 行注释，共 {total_count} 行代码")


def test():
    """测试函数"""
    print("测试移除 tests/examples/example2.py 文件的注释")
    py_file_path = Path("tests/examples/example2.py")
    RemoveSinglePyFileNotes(py_file_path)


if __name__ == "__main__":
    test()
