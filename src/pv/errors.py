"""编程可视化工具的自定义异常类。"""


class PVError(Exception):
    """所有 harness 异常的基类。"""

    def __init__(self, message: str, detail: str = "", user_message: str = ""):
        self.message = message
        self.detail = detail
        self.user_message = user_message or message
        super().__init__(message)


class ProblemLoadError(PVError):
    """problem.json 无法读取或解析。"""

    def __init__(self, message: str = "", detail: str = "", user_message: str = ""):
        message = message or "无法读取或解析 problem.json 文件。"
        user_message = user_message or "题目配置文件加载失败，请检查 problem.json 文件是否存在且格式正确。"
        super().__init__(message, detail, user_message)


class CasesLoadError(PVError):
    """cases.json 无法读取或解析。"""

    def __init__(self, message: str = "", detail: str = "", user_message: str = ""):
        message = message or "无法读取或解析 cases.json 文件。"
        user_message = user_message or "测试用例文件加载失败，请检查 cases.json 文件是否存在且格式正确。"
        super().__init__(message, detail, user_message)


class ProblemMetaInvalid(PVError):
    """problem.json 缺少必要字段或字段类型不对。"""

    def __init__(self, message: str = "", detail: str = "", user_message: str = ""):
        message = message or "problem.json 缺少必要字段或字段类型不正确。"
        user_message = user_message or "题目配置信息不完整，请检查 problem.json 中的字段是否齐全且格式正确。"
        super().__init__(message, detail, user_message)


class CasesInvalid(PVError):
    """cases.json 格式不对，如不是 list、缺 args 等。"""

    def __init__(self, message: str = "", detail: str = "", user_message: str = ""):
        message = message or "cases.json 格式不正确。"
        user_message = user_message or "测试用例格式不正确，请检查 cases.json 文件的内容格式。"
        super().__init__(message, detail, user_message)


class SolutionImportError(PVError):
    """无法导入 solution.py。"""

    def __init__(self, message: str = "", detail: str = "", user_message: str = ""):
        message = message or "无法导入 solution.py 模块。"
        user_message = user_message or "代码文件加载失败，请检查 solution.py 文件是否存在且没有语法错误。"
        super().__init__(message, detail, user_message)


class ClassNotFoundError(PVError):
    """在 solution 模块中找不到指定 class。"""

    def __init__(self, message: str = "", detail: str = "", user_message: str = ""):
        message = message or "在 solution 模块中找不到指定的类。"
        user_message = user_message or "在 solution 文件中找不到指定的类。请检查文件名和类名是否匹配。"
        super().__init__(message, detail, user_message)


class MethodNotFoundError(PVError):
    """在 Solution 实例中找不到指定 method。"""

    def __init__(self, message: str = "", detail: str = "", user_message: str = ""):
        message = message or "在 Solution 实例中找不到指定的方法。"
        user_message = user_message or "在 Solution 类中找不到指定的方法。请检查方法名是否拼写正确。"
        super().__init__(message, detail, user_message)


class CaseExecutionError(PVError):
    """method 运行时抛出了异常。"""

    def __init__(self, message: str = "", detail: str = "", user_message: str = ""):
        message = message or "代码运行时抛出了异常。"
        user_message = user_message or "代码运行时出错了。请检查代码逻辑。"
        super().__init__(message, detail, user_message)


class CheckerError(PVError):
    """checker 执行失败。"""

    def __init__(self, message: str = "", detail: str = "", user_message: str = ""):
        message = message or "checker 执行失败。"
        user_message = user_message or "结果检查程序出错了。请检查 checker 配置是否正确。"
        super().__init__(message, detail, user_message)


class AdapterError(PVError):
    """适配器转换失败。"""

    def __init__(self, message: str = "", detail: str = "", user_message: str = ""):
        message = message or "适配器转换失败。"
        user_message = user_message or "数据转换出错了。请检查适配器配置是否正确。"
        super().__init__(message, detail, user_message)


class TraceLimitExceeded(PVError):
    """trace event 数量超过 max_events。"""

    def __init__(self, message: str = "", detail: str = "", user_message: str = ""):
        message = message or "trace event 数量超过 max_events 限制。"
        user_message = user_message or "代码执行步骤过多，可能陷入了死循环。请检查代码中的循环逻辑。"
        super().__init__(message, detail, user_message)
