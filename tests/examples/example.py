#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块级别的文档字符串。

这是一个示例模块，用于测试注释统计和移除功能。
它包含了各种类型的注释和代码结构。
"""

"""
123
"""
# 标准库导入
import os
from typing import Dict, List

# 第三方库导入
from loguru import logger  # 日志记录

# 常量定义
MAX_RETRIES = 3  # 最大重试次数
DEFAULT_TIMEOUT = 30  # 默认超时时间
API_BASE_URL = "https://api.example.com"  # API基础URL

"""
这是一个独立的多行字符串注释。
它可以跨越多行，并且通常用于模块级别的文档。
"""


class ExampleClass:
    """
    示例类的文档字符串。

    这个类展示了各种注释和代码模式。
    """

    class_attribute = "类属性"  # 类属性注释

    def __init__(self, name: str, value: int = 0):
        """
        初始化方法。

        Args:
            name: 实例名称
            value: 初始值，默认为0
        """
        self.name = name
        self.value = value
        self._private_var = "私有变量"  # 私有变量注释

    def public_method(self, input_data: Dict) -> str:
        """
        公共方法的文档字符串。

        Args:
            input_data: 输入数据字典

        Returns:
            处理后的字符串结果
        """
        # 方法实现开始
        if not input_data:  # 检查输入是否为空
            return "空输入"  # 返回默认值

        result = ""
        for key, value in input_data.items():  # 遍历字典项
            # 处理每个键值对
            processed = f"{key}: {value}"  # 格式化字符串
            result += processed + "\n"  # 添加到结果

        return result.strip()  # 返回去除空白的结果

    def _private_method(self) -> None:
        """私有方法的文档字符串。"""
        # 这是一个私有方法，外部不应该调用
        logger.debug("私有方法被调用")  # 调试日志

    @classmethod
    def class_method(cls) -> int:
        """
        类方法的文档字符串。

        Returns:
            返回一个固定值
        """
        return 42  # 生命、宇宙及一切问题的答案

    @staticmethod
    def static_method(number: int) -> bool:
        """
        静态方法的文档字符串。

        Args:
            number: 输入数字

        Returns:
            是否为偶数
        """
        return number % 2 == 0  # 检查是否为偶数


def standalone_function(param1: str, param2: int = 10) -> List[str]:
    """
    独立函数的文档字符串。

    这是一个模块级别的函数，不依赖于任何类。

    Args:
        param1: 字符串参数
        param2: 整数参数，默认为10

    Returns:
        字符串列表
    """
    results = []
    for i in range(param2):  # 循环param2次
        # 生成结果项
        item = f"{param1}_{i}"  # 格式化字符串
        results.append(item)

        # 每5次记录一次日志
        if i % 5 == 0:  # 检查是否为5的倍数
            logger.info(f"处理第 {i} 项")  # 信息日志

    return results


# 全局变量定义
global_counter = 0  # 全局计数器
CONFIG = {  # 配置字典
    "debug": True,  # 调试模式
    "max_items": 100,  # 最大项目数
    "api_key": os.getenv("API_KEY", "default_key"),  # API密钥
}

"""
另一个独立的多行字符串注释。
用于测试多个独立注释的情况。
"""


def function_with_complex_logic():
    """
    包含复杂逻辑和多种注释的函数。

    这个函数展示了各种代码结构和注释模式。
    """
    # 条件语句示例
    if CONFIG["debug"]:  # 检查调试模式
        logger.debug("调试模式已启用")  # 调试信息
        # 设置详细日志级别
        log_level = "DEBUG"  # 日志级别
    else:
        log_level = "INFO"  # 默认日志级别

    # 循环示例
    items = []  # 初始化空列表
    for i in range(10):  # 循环10次
        if i % 2 == 0:  # 检查是否为偶数
            items.append(f"even_{i}")  # 添加偶数项
        else:
            items.append(f"odd_{i}")  # 添加奇数项

        # 内联注释示例
        if i == 5:  # 中间点
            logger.info("达到中间点")  # 信息日志

    # 列表推导式示例
    squared = [x**2 for x in range(5)]  # 计算平方数

    # 字典示例
    mapping = {
        "name": "Example",  # 名称
        "version": "1.0",  # 版本
        "active": True,  # 激活状态
    }

    # 返回结果
    return {
        "log_level": log_level,  # 日志级别
        "items": items,  # 项目列表
        "squared": squared,  # 平方数列表
        "mapping": mapping,  # 映射字典
    }


def function_with_multiline_strings():
    """
    包含多行字符串的函数。

    这个函数展示了代码中的多行字符串，这些不应该被识别为注释。
    """
    # 多行字符串作为变量
    html_template = """
    <html>
        <head>
            <title>示例页面</title>
        </head>
        <body>
            <h1>Hello World</h1>
        </body>
    </html>
    """

    # SQL查询示例
    sql_query = """
    SELECT *
    FROM users
    WHERE active = TRUE
    AND created_at > '2023-01-01'
    ORDER BY created_at DESC
    """

    # 多行f-string
    name = "Alice"
    age = 30
    message = f"""
    亲爱的{name}:

    感谢您使用我们的服务。
    您的年龄是{age}岁。

    此致
    敬礼
    """

    return {
        "html": html_template,  # HTML模板
        "sql": sql_query,  # SQL查询
        "message": message,  # 消息
    }


# 条件执行块
if __name__ == "__main__":  # 主程序入口
    # 创建实例
    example = ExampleClass("测试实例")  # 示例实例

    # 调用方法
    data = {"key1": "value1", "key2": "value2"}  # 测试数据
    result = example.public_method(data)  # 调用公共方法
    print(result)  # 打印结果

    # 调用独立函数
    items = standalone_function("test", 5)  # 调用独立函数
    print(items)  # 打印结果

    # 调用复杂函数
    complex_result = function_with_complex_logic()  # 调用复杂函数
    print(complex_result)  # 打印结果

    # 记录完成信息
    logger.success("程序执行完成")  # 成功日志

"""
最后的独立多行注释。

这个文件包含了各种注释和代码模式，用于测试注释统计和移除功能。
包括：
- 单行注释
- 文档字符串
- 独立的多行字符串注释
- 代码中的多行字符串
- 各种代码结构中的注释
"""

# 文件结束注释
