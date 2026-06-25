# 学习者提交模式

本工具支持三种提交模式，分别对应不同的学习场景。

---

## 1. 课程参考可视化（Lesson / Reference Visualization）

**文件**: `visual_solution.py`（含 trace hooks）

**原理**: 参考解答中内嵌了追踪钩子（trace hooks），在每次指针移动、比较、状态变更时主动发出语义化事件。

**输出**: 完整的语义化执行轨迹，包含每一步的算法细节。

**适用场景**: 学习算法的执行过程，理解每一步在做什么。

**示例**:

```bash
uv run python -m pv run problems/0001_two_sum --solution visual_solution.py --save-trace
```

**轨迹特点**:
- 每个事件都有 `event`、`state`、`message` 字段
- 渲染器可以展示指针移动、变量变化、数据结构状态
- 消息面向初学者，解释"为什么这样做"而非仅展示"做了什么"

---

## 2. 学习者验证（Learner Validation）

**文件**: `solution.py`（用户自己写的代码，不含 trace hooks）

**原理**: 运行器仍然会加载并执行你的代码，验证输出是否正确，但不会产生语义化轨迹事件。

**输出**: 仅记录输入、输出、通过/失败状态。无逐步执行细节。

**适用场景**: 检查自己的代码是否能通过测试用例。

**示例**:

```bash
uv run python -m pv run problems/0206_reverse_linked_list --solution my_solution.py
```

**行为**:
- 加载 `my_solution.py` 中的 `Solution` 类
- 依次运行 `cases.json` 中的测试用例
- 报告每个用例的通过/失败状态
- 不会生成 trace 文件（除非同时指定 `--save-trace`，此时进入降级追踪模式）

---

## 3. 降级追踪（Fallback Trace）

**触发条件**: 学习者的代码没有 trace hooks，但命令中指定了 `--save-trace`。

**原理**: 当无法从代码中获取语义化事件时，生成一个最小化轨迹，仅包含运行元信息。

**输出**: 仅包含以下字段的最小轨迹：

```json
{
  "trace_mode": "validation_only",
  "problem": "0206_reverse_linked_list",
  "method": "reverseList",
  "input": [1, 2, 3, 4, 5],
  "output": [5, 4, 3, 2, 1],
  "status": "accepted",
  "error": null
}
```

**适用场景**: 需要保存运行记录，但代码中没有追踪钩子。

**设计原则**:
- **不伪造语义事件** — 不假装知道代码内部在做什么
- 标记 `"trace_mode": "validation_only"`，让渲染器知道这是有限信息
- 渲染器遇到 validation_only 轨迹时应提示用户：如需完整可视化，请使用 `visual_solution.py`

---

## 模式对比

| 特性 | 课程参考可视化 | 学习者验证 | 降级追踪 |
|------|---------------|-----------|---------|
| 输入文件 | `visual_solution.py` | 用户的 `solution.py` | 用户的 `solution.py` |
| 含 trace hooks | 是 | 否 | 否 |
| 语义化事件 | 完整 | 无 | 无 |
| 输出验证 | 是 | 是 | 是 |
| 轨迹文件 | 完整轨迹 | 不生成 | 最小轨迹 |
| `trace_mode` | `"semantic"` | `"none"` | `"validation_only"` |

---

## Import 策略

在运行学习者代码之前，工具会进行 **导入预检（pre-flight check）**，扫描代码中的 `import` 语句，判断是否允许使用。

> **重要提示**: 这不是安全沙箱（sandbox）。它只是面向教育场景的预检机制，帮助学习者了解哪些库适合算法练习代码。

### 允许的标准库（STDLIB_ALLOW）

以下 Python 标准库模块可以在提交代码中使用：

`typing` · `collections` · `math` · `functools` · `itertools` · `heapq` · `bisect` · `random` · `string` · `re` · `enum` · `dataclasses` · `copy` · `operator`

这些模块在算法练习中常用，不会产生副作用。

### 禁止的模块（BLOCKED）

以下模块涉及系统访问，在算法练习中不需要：

`os` · `sys` · `subprocess` · `socket` · `shutil` · `pathlib` · `glob` · `platform` · `ctypes` · `signal`

**原因**: 算法练习代码不需要文件系统操作、进程管理或网络通信。

### 不支持的第三方库（UNSUPPORTED）

以下第三方库不在运行环境中，无法导入：

`numpy` · `pandas` · `torch` · `tensorflow` · `scipy` · `sklearn` · `matplotlib` · `seaborn` · `plotly`

**原因**: 本工具只使用 Python 标准库，不安装第三方数据处理或机器学习库。请用纯 Python 实现算法。

### 未列出的模块

如果导入的模块不在上述任何一个列表中，工具会发出 **警告（warning）** 但不会阻止运行。运行时如果出错，请检查该模块是否可用。

### 检查方式

导入检查通过 AST（抽象语法树）解析完成，仅分析源码中的 `import` 和 `from ... import` 语句。提取到最顶层包名（`.` 之前的部分）后进行匹配。

```python
# 例如：
import os.path     → 检查 "os"
from collections import defaultdict → 检查 "collections"
import numpy as np → 检查 "numpy"
```
