# Harness Plan

> Version: 0.1.0 — first version, before any implementation.
> 本文档是 harness 的完整规划，内容足够具体，可以指导下一轮直接开始实现。

---

## 1. Harness 职责边界

### 1.1 第一版要实现

| 职责 | 说明 |
|------|------|
| 加载问题目录 | 接收 `problems/0001_two_sum/` 路径，读取 `problem.json`、`cases.json` |
| 读取问题元数据 | 从 `problem.json` 获取 class_name、method_name、pattern_tags、checker 等 |
| 读取 `cases.json` | 解析所有测试用例 |
| 导入 `solution.py` 或 `visual_solution.py` | 动态 import，隔离 module cache |
| 实例化 `Solution` | 每个 case 执行前重新实例化 |
| 调用指定方法 | 按 method_name 反射调用，支持 keyword/positional args |
| 处理参数适配 | 将 cases.json 中的 JSON 结构反序列化为 Python 对象（数组、链表、树等） |
| 标准化返回值 | 将返回值序列化回 JSON 可比较形式 |
| 校验 expected | 用精确相等或自定义 checker |
| 支持自定义 checker | 支持 `checker_name` 指定，内置 checker 在 `checkers.py` |
| 收集 trace events | 通过 `TraceBuilder` 提供给 `visual_solution.py` |
| 输出运行结果 | 打印每个 case 的 pass/fail、message |
| 保存 trace JSON | 写入 `problems/XXXX_YYY/trace.case{N}.json` |

### 1.2 第一版不实现

| 不做什么 | 为什么 |
|----------|--------|
| 生产级 sandbox | 只跑 curated reference solution，不是任意用户代码 |
| 运行陌生用户任意代码 | 不提供 web 提交 |
| 多语言支持 | 第一版只支持 Python |
| 隐藏测试 | 所有 case 对学习者完全可见 |
| 抓取 LeetCode | 不复制 LeetCode 内容 |
| 复制官方题面 / 样例 / 题解 | 所有 problem 内容原创 |
| 完整前端 | 第一版只做文本输出 + trace JSON |
| 重量级依赖 | 零外部 pip 依赖，纯 stdlib |
| Web 服务 / API | 只做 CLI |
| 性能优化（加速、缓存、并行） | 第一版单线程顺序执行即可 |

---

## 2. 推荐目录结构

### 2.1 最终文件树

```text
programming-visualization/
├── src/
│   └── pv/
│       ├── __init__.py
│       ├── harness.py           # 核心：加载 problem，运行 cases，校验，保存 trace
│       ├── trace_schema.py      # TraceBuilder + TraceEvent 数据类
│       ├── checkers.py          # 内置 checker 函数集合
│       ├── adapters.py          # 输入/输出适配器（array, linked_list, tree, grid）
│       ├── structures.py        # ListNode, TreeNode 等数据结构定义
│       ├── errors.py            # 所有自定义异常 + 人类可读 message
│       ├── render_text.py       # 文本播放器：把 trace JSON 渲染为可读文本
│       └── cli.py               # argparse CLI 入口
├── problems/
│   └── 0001_two_sum/
│       ├── problem.json
│       ├── solution.py
│       ├── visual_solution.py
│       ├── cases.json
│       ├── explain.md
│       └── trace.sample.json
└── tests/
    ├── test_harness.py
    ├── test_checkers.py
    ├── test_adapters.py
    ├── test_trace_schema.py
    ├── test_render_text.py
    └── test_two_sum_e2e.py
```

### 2.2 为什么用 `src/pv` 而不是 `packages/engine_py`

- AGENTS.md、README.md 已经约定使用 `src/pv/`，直接沿用即可。
- 第一版只有一个 Python 包，不需要 `packages/` 这种多包容器的复杂度。
- 保持与现有文档一致，降低新贡献者的理解成本。

### 2.3 文件职责速查

| 文件 | 职责 | 行数预估 |
|------|------|----------|
| `trace_schema.py` | TraceBuilder、TraceEvent 数据类、序列化 | ~120 行 |
| `checkers.py` | CheckResult、内置 checker 函数 | ~80 行 |
| `structures.py` | ListNode、TreeNode 定义 | ~40 行 |
| `adapters.py` | 输入反序列化 + 输出序列化 | ~120 行 |
| `harness.py` | 核心编排逻辑 | ~180 行 |
| `errors.py` | 自定义异常 | ~60 行 |
| `render_text.py` | 文本播放器 | ~80 行 |
| `cli.py` | argparse 入口 | ~60 行 |
| **总计** | | **~740 行** |

这个量级完全适合一人实现，不需要拆分多个 Agent。

---

## 3. Problem Package Contract

### 3.1 最小文件契约

每个题目目录必须包含以下文件：

```text
problems/0001_two_sum/
├── problem.json          # 必须：问题元数据
├── solution.py           # 必须：干净解法
├── visual_solution.py    # 必须：带 trace 的解法
├── cases.json            # 必须：本地测试用例
├── explain.md            # 必须：面向初学者的解释
└── trace.sample.json     # 可选但推荐：预生成的 trace 样例
```

### 3.2 `problem.json` 字段设计

```json
{
  "problem_id": "0001_two_sum",
  "display_title": "Two Sum",
  "pattern_tags": ["array", "hash_map"],
  "difficulty": "easy",
  "entry": {
    "class_name": "Solution",
    "method_name": "twoSum"
  },
  "input_schema": {
    "type": "object",
    "fields": [
      {"name": "nums", "type": "array", "items": "int"},
      {"name": "target", "type": "int"}
    ]
  },
  "output_schema": {
    "type": "array",
    "items": "int",
    "description": "indices of the two numbers"
  },
  "checker": {
    "name": "unordered_pairs",
    "description": "order of the two indices does not matter"
  },
  "adapter": {
    "input": {
      "nums": {"kind": "builtin", "hint": "list[int]"}
    },
    "output": {"kind": "builtin", "hint": "list[int]"}
  },
  "limits": {
    "max_events": 1000
  },
  "reference": {
    "platform": "LeetCode",
    "id": 1,
    "title": "Two Sum",
    "usage": "compatibility reference only"
  }
}
```

#### 字段说明

| 字段 | 必须 | 类型 | 说明 |
|------|------|------|------|
| `problem_id` | 是 | string | 唯一标识，与目录名一致 |
| `display_title` | 推荐 | string | 人类可读标题（缺失时 fallback 到 problem_id） |
| `pattern_tags` | 是 | string[] | 从 AGENTS.md 的 pattern buckets 选取 |
| `difficulty` | 是 | enum | `"easy"` / `"medium"` / `"hard"` |
| `entry.class_name` | 是 | string | Python class 名称，如 `"Solution"` |
| `entry.method_name` | 是 | string | 要调用的方法名，如 `"twoSum"` |
| `input_schema` | 推荐 | object | 描述每个 case 的 args 结构，用于校验 |
| `output_schema` | 推荐 | object | 描述返回值结构 |
| `checker` | 否 | object | 默认 `exact`，自定义时指定 name |
| `adapter` | 否 | object | 声明哪些参数需要适配器转换；省略则全部当 builtin 处理 |
| `limits.max_events` | 否 | int | 每个 case 最大 trace event 数，默认 10000 |
| `reference` | 否 | object | 外部平台引用，仅用于兼容性标记 |

#### checker.name 取值

| 值 | 说明 |
|----|------|
| `exact` | 默认，精确相等 |
| `unordered_array` | 无序数组比较 |
| `unordered_pairs` | 两个元素为一组，组内无序 |
| `unordered_triplets` | 三个元素为一组，组内无序 |
| `set_of_sorted_arrays` | 集合中的每个元素是一个排序后的数组 |
| `linked_list_equal` | 链表逐节点相等 |
| `tree_level_order_equal` | 二叉树按层序相等 |

不指定 `checker` 或 `checker.name` 为 `"exact"` 时，用 `==` 比较。

#### adapter 说明

`adapter.input` 的 key 对应 `cases.json` 中 `args` 的字段名。value 指定 `kind`：

| kind | 说明 | Phase |
|------|------|-------|
| `builtin` | Python 原生类型 (int, str, list, bool, None) | Phase 1 |
| `linked_list` | 从数组构建带 next 的链表 | Phase 2 |
| `tree` | 从层序列构建二叉树 | Phase 3 |

### 3.3 `cases.json` 格式

```json
[
  {
    "name": "basic example",
    "args": {
      "nums": [2, 7, 11, 15],
      "target": 9
    },
    "expected": [0, 1],
    "notes": "The answer appears after one hash-map lookup."
  },
  {
    "name": "answer reversed",
    "args": {
      "nums": [3, 2, 4],
      "target": 6
    },
    "expected": [1, 2],
    "notes": "Order does not matter — checker handles unordered comparison."
  },
  {
    "name": "same value twice",
    "args": {
      "nums": [3, 3],
      "target": 6
    },
    "expected": [0, 1],
    "notes": "Edge case: duplicate values."
  }
]
```

#### `cases.json` 字段说明

| 字段 | 必须 | 类型 | 说明 |
|------|------|------|------|
| `name` | 是 | string | case 名称，用于报告 |
| `args` | 是 | object | 传给 method 的参数，key 对应 method 参数名 |
| `expected` | 是 | any | 期望输出 |
| `notes` | 否 | string | 教学注释 |

#### args 传递规则

- 默认情况下，harness 按 `args` 的 key 作为 keyword argument 传递。
- 如果 method 的参数名与 `args` key 一致，直接用 keyword。
- 如果 method 接受 `*args` 或 `**kwargs`，按 case 的 args 结构匹配。
- 第一版简化：只支持 keyword args，且 case 的 args key 必须完全匹配 method 的参数名。

### 3.4 trace 输出文件

每次运行后，trace 保存在题目目录下：

```text
problems/0001_two_sum/trace.case0.json
problems/0001_two_sum/trace.case1.json
problems/0001_two_sum/trace.case2.json
```

文件名格式：`trace.case{N}.json`，N 是 case 在 cases.json 中的索引。

---

## 4. Solution 调用机制

### 4.1 动态 import

```python
# harness.py 核心流程
import importlib.util
import uuid

def load_solution(file_path: str) -> type:
    """从指定 .py 文件加载 Solution class."""
    module_name = f"pv_dynamic_{uuid.uuid4().hex[:8]}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

要点：

- 使用 `uuid` 或 `hash(file_path)` 生成唯一 module_name，防止多次加载同一文件时 module cache 污染。
- 只加载 `solution.py` 或 `visual_solution.py`，不同时加载两个。
- 如果文件不存在，抛出 `ProblemLoadError`。

### 4.2 实例化与调用

```python
def run_case(problem_meta, case, solution_path):
    # 1. 动态加载 module
    module = load_solution(solution_path)

    # 2. 查找 class
    class_name = problem_meta["entry"]["class_name"]
    if not hasattr(module, class_name):
        raise ClassNotFoundError(class_name)

    # 3. 实例化 (每个 case 都重新实例化)
    instance = getattr(module, class_name)()

    # 4. 查找 method
    method_name = problem_meta["entry"]["method_name"]
    if not hasattr(instance, method_name):
        raise MethodNotFoundError(method_name)

    method = getattr(instance, method_name)

    # 5. 适配输入参数
    args = adapt_input(case["args"], problem_meta.get("adapter"))

    # 6. 执行
    try:
        result = method(**args)
    except Exception as e:
        # 捕获并包装为用户可读错误
        raise CaseExecutionError(e)

    # 7. 序列化结果
    normalized = adapt_output(result, problem_meta.get("adapter"))

    # 8. 校验
    check_result = check(normalized, case["expected"],
                         checker_name=problem_meta.get("checker", {}).get("name", "exact"))

    return CaseResult(
        run_id=str(uuid.uuid4())[:8],
        case_name=case["name"],
        passed=check_result.passed,
        actual=normalized,
        expected=case["expected"],
        message=check_result.message,
        error=None,
        trace=...,  # 从 TraceBuilder 获取
    )
```

### 4.3 关键设计决策

| 决策 | 结论 | 理由 |
|------|------|------|
| 每个 case 重新实例化 Solution | 是 | 避免 state 泄漏 |
| 每个 case 单独 run_id | 是 | 日志/文件可追溯 |
| 异常捕获后是否继续执行后续 case | 继续 | 学习者需要看到每个 case 的结果 |
| 如何把 TraceBuilder 传给 visual_solution | 通过构造函数参数 `trace` | 显式传参 > 隐式 global |
| trace 收集和校验是否同时进行 | 是 | trace 应记录到最后一刻（包括报错步骤） |

### 4.4 visual_solution.py 约定

```python
# visual_solution.py
class Solution:
    def __init__(self, trace=None):
        self.trace = trace  # TraceBuilder 实例

    def twoSum(self, nums, target):
        seen = {}
        for i, num in enumerate(nums):
            self.trace.event(
                event_type="array_read",
                message=f"读取 nums[{i}] = {num}",
                highlight={"objects": ["arr:nums"], "indices": {"arr:nums": [i]}},
                before={"i": i, "num": num},
            )
            complement = target - num
            self.trace.event(
                event_type="hash_map_get",
                message=f"检查补数 {complement} 是否在哈希表中",
                before={"complement": complement, "map:seen": dict(seen)},
            )
            if complement in seen:
                self.trace.event(
                    event_type="answer_found",
                    message=f"找到！{complement} 在索引 {seen[complement]}，当前索引 {i}",
                    highlight={"objects": ["map:seen"], "indices": {}},
                    after={"result": [seen[complement], i]},
                )
                return [seen[complement], i]
            seen[num] = i
            self.trace.event(
                event_type="hash_map_put",
                message=f"将 {num} -> 索引 {i} 存入哈希表",
                highlight={"objects": ["map:seen"]},
                before={"map:seen": dict(seen)},
                after={"map:seen": dict(seen)},
            )
        return []
```

要点：
- `trace` 通过 `__init__(self, trace=None)` 接收。`solution.py` 不传 trace 也能正常运行。
- `trace.event()` 如果 trace 为 None（跑 solution.py），静默忽略，不做任何事。
- 第一版不做自动插桩/装饰器，由人工写 `visual_solution.py`。保底简单。

---

## 5. 输入输出适配器 (adapters)

### 5.1 设计原则

- `case.json` 中 args 直接写 JSON 结构。
- 如果某个参数声明了 `"kind": "linked_list"`，harness 调用 method 前自动从 `[1, 2, 3]` 构造 ListNode 链表。
- 返回值也自动序列化回 json 可比较形式。

### 5.2 数据结构定义 (`structures.py`)

```python
# 第一版只定义这两个
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
```

### 5.3 实现优先级

| Phase | 适配类型 | adapter kind | JSON 表示 | Python 构造 | 返回值序列化 |
|-------|---------|-------------|-----------|-------------|-------------|
| 1 | array | `builtin` | `[1, 2, 3]` | 直接用 | 直接用 |
| 1 | number | `builtin` | `42` | 直接用 | 直接用 |
| 1 | string | `builtin` | `"hello"` | 直接用 | 直接用 |
| 1 | grid (2D array) | `builtin` | `[[1,2],[3,4]]` | 直接用 | 直接用 |
| 2 | linked list | `linked_list` | `[1, 2, 3]` | `ListNode(1, ListNode(2, ListNode(3)))` | `[1, 2, 3]` |
| 3 | binary tree | `tree` | `[3, 9, 20, null, null, 15, 7]` | `TreeNode` 树 | `[3, 9, 20, null, null, 15, 7]` |

### 5.4 适配器接口

```python
# adapters.py

def adapt_input(args: dict, adapter_config: dict | None) -> dict:
    """将 cases.json 的 args 从 JSON 结构转换为 Python 对象。"""
    if not adapter_config or "input" not in adapter_config:
        return args
    result = dict(args)
    for key, spec in adapter_config.get("input", {}).items():
        if key in result:
            result[key] = _deserialize(result[key], spec["kind"])
    return result

def adapt_output(value, adapter_config: dict | None):
    """将 Python 返回值序列化回 JSON 可比较形式。"""
    if not adapter_config or "output" not in adapter_config:
        return value
    spec = adapter_config["output"]
    return _serialize(value, spec["kind"])

def _deserialize(raw, kind: str):
    if kind == "builtin":
        return raw
    elif kind == "linked_list":
        return _build_linked_list(raw)
    elif kind == "tree":
        return _build_tree(raw)
    else:
        raise AdapterError(f"Unknown input kind: {kind}")

def _serialize(value, kind: str):
    if kind == "builtin":
        return value
    elif kind == "linked_list":
        return _list_from_linked_list(value)
    elif kind == "tree":
        return _list_from_tree(value)
    else:
        raise AdapterError(f"Unknown output kind: {kind}")
```

### 5.5 Phase 1（只做 builtin）

Phase 1 中，不区分 adapter，所有东西当 `builtin` 处理。此时 `cases.json` 的 args 直接传给 method，返回值直接用 `==` 比较。

Phase 1 的 `adapt_input` 和 `adapt_output` 是 no-op。实际的适配逻辑在 Phase 2（linked list）和 Phase 3（tree）才加入。

---

## 6. Checker 设计

### 6.1 接口

```python
# checkers.py

from dataclasses import dataclass
from typing import Any

@dataclass
class CheckResult:
    passed: bool
    expected: Any
    actual: Any
    normalized_expected: Any   # checker 标准化后的 expected
    normalized_actual: Any     # checker 标准化后的 actual
    message: str               # 给用户的说明


def check(actual, expected, checker_name: str = "exact", context: dict | None = None) -> CheckResult:
    """
    主入口。根据 checker_name 调用对应的 checker 函数。

    context 保留用于未来的自定义 checker（如传入 problem 元信息）。
    """
    checker = _CHECKERS.get(checker_name)
    if checker is None:
        raise CheckerError(f"Unknown checker: {checker_name}")
    return checker(actual, expected)
```

### 6.2 内置 checker 列表

| checker_name | 逻辑 | 示例 |
|-------------|------|------|
| `exact` | `actual == expected` | `[0,1] == [0,1]` |
| `unordered_array` | 排序后比较 | `sorted(actual) == sorted(expected)` |
| `unordered_pairs` | 每对内部排序，整体排序后比较 | `[[0,1],[1,2]]` 与 `[[2,1],[1,0]]` 相等 |
| `unordered_triplets` | 每组三个元素内部排序，整体排序后比较 | 用于 3Sum |
| `set_of_sorted_arrays` | 每个元素排序后集合比较 | 用于排列类问题 |
| `linked_list_equal` | 逐个节点比较 val | 用于链表题 |
| `tree_level_order_equal` | 层序列表比较 | 用于二叉树题 |

### 6.3 Phase 1 优先级

Phase 1 只实现 `exact` 和 `unordered_pairs`（Two Sum 需要）。其余在后续按需添加。

### 6.4 CheckResult 示例

```python
# exact, passed
CheckResult(
    passed=True,
    expected=[0, 1],
    actual=[0, 1],
    normalized_expected=[0, 1],
    normalized_actual=[0, 1],
    message="输出与预期完全一致。"
)

# exact, failed
CheckResult(
    passed=False,
    expected=[0, 1],
    actual=[1, 0],
    normalized_expected=[0, 1],
    normalized_actual=[1, 0],
    message="输出与预期不符。预期 [0, 1]，实际得到 [1, 0]。"
)

# unordered_pairs, passed
CheckResult(
    passed=True,
    expected=[0, 1],
    actual=[1, 0],
    normalized_expected=[[0, 1]],
    normalized_actual=[[0, 1]],
    message="输出顺序不影响结果，索引对一致。"
)
```

---

## 7. Trace Collector 接口

### 7.1 TraceBuilder API

基于 `docs/trace-schema.md` 的规范，实现最小 API：

```python
# trace_schema.py

import time, json
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class TraceEvent:
    step: int
    event_type: str
    message: str
    phase: str = "execute"
    highlight: dict | None = None
    before: dict | None = None
    after: dict | None = None
    pedagogy: dict | None = None
    line: dict | None = None
    timestamp_ms: int = 0


class TraceBuilder:
    def __init__(self, problem_meta: dict, case: dict, max_events: int = 10000):
        self._problem_meta = problem_meta
        self._case = case
        self._max_events = max_events
        self._events: list[TraceEvent] = []
        self._step = 0
        self._truncated = False
        self._finished = False
        self._result_status = "running"
        self._result_actual = None

    def event(self, event_type: str, message: str,
              highlight: dict = None, before: dict = None, after: dict = None,
              pedagogy: dict = None, line: dict = None):
        """录制一个 trace event。如果超过 max_events，静默丢弃并标记 truncated。"""
        if self._finished:
            return
        if self._step >= self._max_events:
            self._truncated = True
            return
        self._step += 1
        self._events.append(TraceEvent(
            step=self._step,
            event_type=event_type,
            message=message,
            highlight=highlight,
            before=before,
            after=after,
            pedagogy=pedagogy,
            line=line,
            timestamp_ms=int(time.time() * 1000),
        ))

    def finish(self, status: str, actual: Any):
        """标记 trace 完成，记录最终结果。"""
        self._result_status = status
        self._result_actual = actual
        self._finished = True

    def to_dict(self) -> dict:
        """生成完整的 trace envelope dict。"""
        return {
            "trace_version": "0.1.0",
            "problem": self._problem_meta,
            "run": {
                "language": "python",
                "entry": self._problem_meta.get("entry", {}),
                "input": self._case.get("args", {}),
                "expected": self._case.get("expected"),
                "actual": self._result_actual,
                "status": self._result_status,
                "total_steps": self._step,
                "truncated": self._truncated,
            },
            "events": [asdict(e) for e in self._events],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, default=str)

    @property
    def step_count(self) -> int:
        return self._step
```

### 7.2 第一版简化决策

| 决策 | 说明 |
|------|------|
| 不实现 `state_patch` | Phase 1 只用 `before` / `after` 快照，够小 |
| 不实现 `objects` 顶层注册表 | visual_solution 内联传 object 状态在 `before`/`after` 中 |
| `line` 字段手动填写 | 不做 AST 行号映射 |
| `timestamp_ms` 自动填充 | 用于后续可能的播放器 |
| trace 为 None 时静默忽略 | `solution.py` 不需要 trace |
| `max_events` 默认 10000 | 可通过 `problem.json` 的 `limits.max_events` 覆盖 |

### 7.3 visual_solution.py 如何获取 TraceBuilder

```python
# harness.py 中
trace = TraceBuilder(problem_meta, case, max_events=...)
instance = SolutionClass(trace=trace)
# 执行 solution
result = method(**adapted_args)
trace.finish(status="passed" if check_ok else "wrong_answer", actual=result)
# 保存 trace
save_trace(trace, output_path)
```

TraceBuilder 通过构造函数显式传入，不用 global/thread-local/context manager。

### 7.4 超限处理

- `max_events` 被超过时：后续 `trace.event()` 静默不记录，并在 `trace.to_dict()` 中设置 `"truncated": true`。
- 不影响正常执行（不抛异常）。
- 运行结束后打印：`"⚠ 跟踪已截断：超过 {max_events} 个事件，可能有无穷循环或跟踪点过多。"`

### 7.5 trace 写入文件

```python
def save_trace(trace: TraceBuilder, output_dir: str, case_index: int):
    """保存 trace JSON 到 problem 目录。"""
    filename = f"trace.case{case_index}.json"
    path = Path(output_dir) / filename
    path.write_text(trace.to_json(), encoding="utf-8")
    return str(path)
```

---

## 8. CLI 规划

### 8.1 目标命令行体验

```bash
# 运行指定 problem 的指定 case
python -m pv run problems/0001_two_sum --case 0

# 运行所有 cases
python -m pv run problems/0001_two_sum --all

# 用 visual solution 运行并保存 trace
python -m pv run problems/0001_two_sum --solution visual_solution.py --save-trace

# 渲染已保存的 trace
python -m pv render-text problems/0001_two_sum/trace.case0.json

# 查看命令帮助
python -m pv --help
```

### 8.2 子命令

| 子命令 | 用途 | 参数 |
|--------|------|------|
| `run` | 运行 problem 的 test cases | `problem_path`, `--case N`, `--all`, `--solution FILENAME`, `--save-trace` |
| `render-text` | 将 trace JSON 渲染为文本说明 | `trace_json_path` |

### 8.3 `run` 命令输出格式

#### 正常通过

```text
============================================================
Problem: Two Sum (0001_two_sum)
Tags: array, hash_map
Difficulty: easy
============================================================

Case 0: basic example .............. PASSED
  输入: nums=[2,7,11,15], target=9
  预期: [0, 1]
  实际: [0, 1]
  事件数: 5

Case 1: answer reversed .............. PASSED
  输入: nums=[3,2,4], target=6
  预期: [1, 2]
  实际: [1, 2]
  事件数: 6

Case 2: same value twice .............. PASSED
  输入: nums=[3,3], target=6
  预期: [0, 1]
  实际: [0, 1]
  事件数: 4

============================================================
结果: 3/3 通过
追踪文件已保存到:
  problems/0001_two_sum/trace.case0.json
  problems/0001_two_sum/trace.case1.json
  problems/0001_two_sum/trace.case2.json
============================================================
```

#### 有失败

```text
Case 0: basic example .............. FAILED
  输入: nums=[2,7,11,15], target=9
  预期: [0, 1]
  实际: None
  错误: 代码抛出了异常 → NameError: name 'sean' is not defined
  事件数: 2 (失败前已追踪)
  提示: 检查是否拼错了变量名。
```

### 8.4 `render-text` 命令输出格式

```text
═══════════════════════════════════
Problem: Two Sum (0001_two_sum)
═══════════════════════════════════

Step 1 | array_read
  读取 nums[0] = 2
  ⚲ 当前值 = 2，需要补数 = 7

Step 2 | hash_map_get
  检查补数 7 是否在哈希表中
  ⚲ 哈希表当前为空 → 没找到

Step 3 | hash_map_put
  将 2 → 索引 0 存入哈希表
  ⚲ 哈希表现在为: {2: 0}

Step 4 | array_read
  读取 nums[1] = 7
  ⚲ 当前值 = 7，需要补数 = 2

Step 5 | hash_map_get
  检查补数 2 是否在哈希表中
  ✓ 找到了！补数 2 在索引 0

Step 6 | answer_found
  返回 [0, 1]
  ✓ 回答正确

───────────────────────────────
结果: passed
实际输出: [0, 1]
预期输出: [0, 1]
───────────────────────────────
```

---

## 9. 错误分类

### 9.1 错误类型定义 (`errors.py`)

```python
# errors.py

class PVError(Exception):
    """所有 harness 异常的基类。"""
    def __init__(self, message: str, detail: str = "", user_message: str = ""):
        self.message = message          # 给开发者
        self.detail = detail            # 额外上下文
        self.user_message = user_message or message  # 给非科班用户看的
        super().__init__(message)


class ProblemLoadError(PVError):
    """problem.json 无法读取或解析。"""
    pass

class CasesLoadError(PVError):
    """cases.json 无法读取或解析。"""
    pass

class ProblemMetaInvalid(PVError):
    """problem.json 缺少必要字段或字段类型不对。"""
    pass

class CasesInvalid(PVError):
    """cases.json 格式不对，如不是 list、缺 args 等。"""
    pass

class SolutionImportError(PVError):
    """无法导入 solution.py。"""
    pass

class ClassNotFoundError(PVError):
    """在 solution 模块中找不到指定 class。"""
    pass

class MethodNotFoundError(PVError):
    """在 Solution 实例中找不到指定 method。"""
    pass

class CaseExecutionError(PVError):
    """method 运行时抛出了异常。"""
    pass

class CheckerError(PVError):
    """checker 执行失败。"""
    pass

class AdapterError(PVError):
    """适配器转换失败。"""
    pass

class TraceLimitExceeded(PVError):
    """trace event 数量超过 max_events。"""
    pass
```

### 9.2 用户可读 message 示例

| 错误场景 | 开发者 message | 用户 message |
|---------|---------------|-------------|
| problem.json 不存在 | `FileNotFoundError: problems/0001_two_sum/problem.json` | `题目 0001_two_sum 缺少 problem.json 文件。这个文件告诉系统题目叫什么、方法名叫什么、怎么判断答案。` |
| class_name 找不到 | `module 'solution' has no attribute 'Soluton'` | `在 solution.py 中找不到类 Soluton。是不是拼写错了？检查 problem.json 的 entry.class_name。` |
| method_name 找不到 | `'Solution' object has no attribute 'twoSUm'` | `Solution 类中没有方法 twoSUm。检查 problem.json 的 entry.method_name 和方法名是否一致。` |
| method 抛异常 | `NameError: name 'sean' is not defined` | `代码运行时出错了：NameError: name 'sean' is not defined。在第 4 行附近，是不是写错了变量名？` |
| 答案不对 | `actual != expected` | `结果与预期不同。预期的答案是 ..., 代码算出来的是 ...。这可能是因为...` |
| checker 不存在 | `Unknown checker: unordered_quadruplets` | `系统不认识 checker unordered_quadruplets。支持的 checker：exact, unordered_array, unordered_pairs。` |
| trace 超限 | `max_events exceeded` | `追踪事件数超过上限 (10000)。可能有无穷循环，或者追踪点写得太多。检查代码是否有死循环。` |
| adapter 不支持 | `Unknown input kind: graph` | `不支持的输入类型 graph。当前支持：builtin, linked_list, tree。` |

---

## 10. 测试计划

### 10.1 测试文件规划

```text
tests/
├── test_trace_schema.py    # TraceBuilder 单元测试
├── test_checkers.py        # Checker 单元测试
├── test_adapters.py        # Adapter 单元测试
├── test_harness.py         # Harness 核心流程测试
├── test_render_text.py     # 文本渲染测试
└── test_two_sum_e2e.py     # Two Sum 端到端测试
```

### 10.2 具体测试用例

#### `test_trace_schema.py`

| 测试 | 输入 | 预期 |
|------|------|------|
| `test_create_trace_builder` | 传入 meta, case | TraceBuilder 初始化成功 |
| `test_add_event_increments_step` | 连续调用 `trace.event()` 3 次 | step 分别为 1, 2, 3 |
| `test_to_dict_contains_envelope` | 完成一次 trace 后 `to_dict()` | 包含 `trace_version`, `problem`, `run`, `events` |
| `test_finish_sets_status` | `trace.finish("passed", [0, 1])` | `run.status == "passed"` |
| `test_max_events_truncates` | max_events=3, 调用 5 次 event | step=3, `truncated=true`, 后续 event 被丢弃 |
| `test_event_after_finish_ignored` | finish 后继续 event | 新 event 不被添加 |
| `test_to_json_serializable` | 复杂 trace | `json.loads(trace.to_json())` 不报错 |

#### `test_checkers.py`

| 测试 | 输入 | 预期 |
|------|------|------|
| `test_exact_pass` | `check([0,1], [0,1], "exact")` | passed=true |
| `test_exact_fail` | `check([0,1], [1,0], "exact")` | passed=false |
| `test_unordered_pairs_pass` | `check([0,1], [1,0], "unordered_pairs")` | passed=true |
| `test_unordered_pairs_multiple` | `check([[0,1],[2,3]], [[3,2],[1,0]], "unordered_pairs")` | passed=true |
| `test_unordered_pairs_fail` | `check([0,1], [0,2], "unordered_pairs")` | passed=false |
| `test_unknown_checker_raises` | `check(x, y, "not_exist")` | CheckerError |

#### `test_adapters.py`

| 测试 | 输入 | 预期 |
|------|------|------|
| `test_builtin_pass_through` | `adapt_input({"nums": [1,2]}, None)` | `{"nums": [1,2]}` |
| `test_linked_list_build` | `adapt_input({"head": [1,2,3]}, {"input": {"head": {"kind": "linked_list"}}})` | head 是 ListNode 链 |
| `test_linked_list_roundtrip` | 构造链表 → 序列化回 list | `[1, 2, 3]` |
| `test_tree_build` | `adapt_input({"root": [1,null,2]}, {"input": {"root": {"kind": "tree"}}})` | root 是 TreeNode |
| `test_tree_roundtrip` | 构造树 → 序列化回 list | `[1, null, 2]` |
| `test_unknown_kind_raises` | `_deserialize(x, "graph")` | AdapterError |

#### `test_harness.py`

| 测试 | 场景 | 预期 |
|------|------|------|
| `test_load_problem_meta` | 读取有效的 problem.json | 返回完整 dict |
| `test_missing_problem_json` | 目录没有 problem.json | ProblemLoadError |
| `test_missing_cases_json` | 目录没有 cases.json | CasesLoadError |
| `test_cases_not_array` | cases.json 是 `{}` | CasesInvalid |
| `test_load_solution` | 加载有效 solution.py | 返回 module 对象 |
| `test_class_not_found` | class_name 拼错 | ClassNotFoundError |
| `test_method_not_found` | method_name 拼错 | MethodNotFoundError |
| `test_run_single_case_pass` | Two Sum case | CaseResult(passed=true) |
| `test_run_single_case_fail` | Two Sum 返回错误结果 | CaseResult(passed=false) |
| `test_state_no_leak` | 连续跑两个 case，第二个 case 不受第一个影响 | 两个 case 独立 |
| `test_custom_checker` | 用 unordered_pairs checker | 顺序不同但 passes |
| `test_exception_in_method` | method 故意写 raise | CaseExecutionError，后续 case 继续跑 |
| `test_trace_saved` | `--save-trace` | trace.case0.json 文件存在且格式合法 |
| `test_trace_on_wrong_answer` | 答案错误时 trace 仍然保存 | trace 文件和状态信息完整 |
| `test_visual_solution_trace` | 加载 visual_solution.py | trace 中有预期的 event_type 序列 |

#### `test_render_text.py`

| 测试 | 输入 | 预期 |
|------|------|------|
| `test_render_basic_trace` | 准备好的 trace JSON | 输出包含 "Step 1" 和 message |
| `test_render_includes_result` | trace with status | 输出包含 "passed" 或 "wrong_answer" |
| `test_render_empty_events_list` | events=[] | 不崩溃，输出 "无追踪事件" |

#### `test_two_sum_e2e.py`

| 测试 | 说明 |
|------|------|
| `test_solution_passes_all_cases` | 用 `solution.py` 跑所有 case，全部 PASS |
| `test_visual_solution_passes_all_cases` | 用 `visual_solution.py` 跑所有 case，全部 PASS |
| `test_visual_solution_trace_has_expected_events` | trace events 中包含 `array_read`, `hash_map_get`, `hash_map_put`, `answer_found` |
| `test_visual_solution_trace_is_deterministic` | 同一 case 跑两次，trace events 完全一致 |
| `test_wrong_solution_fails` | 用故意写错的 solution，得到 FAIL |
| `test_cli_run_command` | `python -m pv run problems/0001_two_sum --all` 正常输出 |

### 10.3 测试运行方式

```bash
# 运行所有测试
python -m pytest tests/ -v

# 只跑特定文件
python -m pytest tests/test_harness.py -v

# 不依赖 pytest，直接跑也可
python -m unittest discover tests/
```

第一版不引入 pytest 依赖。使用标准库 `unittest`。如果团队偏好 pytest，可在后续切换（pytest 兼容 unittest 用例）。

---

## 11. 第一轮实现顺序

以下是精确的实现步骤。每一步说明输入、输出、验收标准。

### Step 1: 写 `src/pv/__init__.py`

- **输入**: 无
- **输出**: 空 `__init__.py`（或带 `__version__`）
- **验收**: `python -c "import pv; print(pv.__version__)"` 正常

### Step 2: 写 `src/pv/errors.py`

- **输入**: 本规划文档第 9 节
- **输出**: 所有自定义异常类，每个带 `user_message`
- **验收**: `from pv.errors import PVError; raise PVError("test", user_message="用户看这个")`

### Step 3: 写 `src/pv/trace_schema.py`

- **输入**: 本规划文档第 7 节 + `docs/trace-schema.md`
- **输出**: `TraceEvent`, `TraceBuilder` 类
- **验收**: 运行 `test_trace_schema.py` 中所有测试通过

### Step 4: 写 `src/pv/checkers.py`

- **输入**: 本规划文档第 6 节
- **输出**: `CheckResult`, `check()` 函数，内置 `exact` + `unordered_pairs` checker
- **验收**: 运行 `test_checkers.py` 中 Phase 1 测试通过

### Step 5: 写 `src/pv/structures.py`

- **输入**: 本规划文档第 5.2 节
- **输出**: `ListNode`, `TreeNode` 类
- **验收**: `ln = ListNode(1, ListNode(2)); ln.next.val == 2`

### Step 6: 写 `src/pv/adapters.py`

- **输入**: 本规划文档第 5 节
- **输出**: Phase 1 只做 builtin pass-through，Phase 2/3 再加 linked_list/tree
- **验收**: `adapt_input({"a": 1}, None)` 返回 `{"a": 1}`（Phase 1 只验证 no-op）

### Step 7: 写 `src/pv/harness.py`

- **输入**: 本规划文档第 1、3、4 节
- **输出**: `load_solution()`, `load_problem_meta()`, `load_cases()`, `run_case()`, `run_all_cases()`
- **验收**: 运行 `test_harness.py` 中除 e2e 外的测试通过

### Step 8: 写 `problems/0001_two_sum/` 完整目录

- **输入**: 本规划文档第 3 节
- **输出**:
  - `problem.json`（按 3.2 节的示例）
  - `solution.py`（干净 Two Sum 解法）
  - `visual_solution.py`（带 trace 的 Two Sum 解法）
  - `cases.json`（按 3.3 节的示例，至少 3 个 case）
  - `explain.md`（面向初学者的解释）
  - `trace.sample.json`（可以先不写，等 Step 10 跑一次后再保存）
- **验收**:
  - `solution.py` 可独立运行正确
  - `visual_solution.py` 可独立运行正确
  - `cases.json` 格式合法

### Step 9: 写 `src/pv/render_text.py`

- **输入**: 本规划文档第 8.4 节
- **输出**: `render_trace_to_text(trace_json: dict) -> str`
- **验收**: 运行 `test_render_text.py` 中测试通过

### Step 10: 写 `src/pv/cli.py`

- **输入**: 本规划文档第 8 节
- **输出**: argparse 入口，支持 `run` 和 `render-text` 子命令
- **验收**:
  ```bash
  python -m pv run problems/0001_two_sum --all
  python -m pv run problems/0001_two_sum --case 0
  python -m pv run problems/0001_two_sum --solution visual_solution.py --save-trace
  python -m pv render-text problems/0001_two_sum/trace.case0.json
  ```
  四条命令都有正确输出。

### Step 11: 写 tests 目录下所有测试文件

- **输入**: 本规划文档第 10 节
- **输出**: 6 个测试文件，覆盖所有单元测试和 e2e
- **验收**: `python -m unittest discover tests/` 全部通过

### Step 12: 更新 `AGENTS.md` 和 `README.md`

- **输入**: 最终实现的目录结构
- **输出**: 更新后的 README（补充 harness 使用说明）和 AGENTS.md（更新已实现状态）
- **验收**: 文档与实际代码一致

### 实现顺序总结

```text
Step 1: __init__.py          (5 分钟)
Step 2: errors.py            (20 分钟)
Step 3: trace_schema.py      (30 分钟)
Step 4: checkers.py          (20 分钟)
Step 5: structures.py        (10 分钟)
Step 6: adapters.py          (20 分钟)
Step 7: harness.py           (60 分钟)
Step 8: 0001_two_sum 目录    (40 分钟)
Step 9: render_text.py       (30 分钟)
Step 10: cli.py              (20 分钟)
Step 11: tests               (60 分钟)
Step 12: 文档更新            (20 分钟)
────────────────────────────────
总计预估: ~5.5 小时
```

### 关键验收门禁

在声称 "harness 完成" 之前，必须通过以下所有检查：

1. [ ] `python -m pv run problems/0001_two_sum --all` 输出 3/3 通过
2. [ ] `python -m pv run problems/0001_two_sum --solution visual_solution.py --save-trace` 生成 `trace.case*.json`
3. [ ] `python -m pv render-text problems/0001_two_sum/trace.case0.json` 输出可读文本
4. [ ] 修改 solution.py 故意返回错误答案时，harness 报告 FAIL 但不崩溃
5. [ ] `python -m unittest discover tests/` 所有测试通过
6. [ ] trace JSON 格式与 `docs/trace-schema.md` 兼容
7. [ ] 零外部 pip 依赖（`pip freeze` 只包含 Python 标准库 + pytest 如果用了的话）

---

## 附录 A: Two Sum problem.json 完整示例

```json
{
  "problem_id": "0001_two_sum",
  "display_title": "两数之和",
  "pattern_tags": ["array", "hash_map"],
  "difficulty": "easy",
  "entry": {
    "class_name": "Solution",
    "method_name": "twoSum"
  },
  "input_schema": {
    "type": "object",
    "fields": [
      {"name": "nums", "type": "array", "items": "int"},
      {"name": "target", "type": "int"}
    ]
  },
  "output_schema": {
    "type": "array",
    "items": "int",
    "minItems": 2,
    "maxItems": 2
  },
  "checker": {
    "name": "unordered_pairs",
    "description": "返回的两个索引顺序不重要"
  },
  "adapter": {
    "input": {
      "nums": {"kind": "builtin"}
    },
    "output": {"kind": "builtin"}
  },
  "limits": {
    "max_events": 1000
  },
  "reference": {
    "platform": "LeetCode",
    "id": 1,
    "title": "Two Sum",
    "usage": "compatibility reference only"
  }
}
```

## 附录 B: Two Sum cases.json 完整示例

```json
[
  {
    "name": "基础示例 — 答案在第一个元素之后",
    "args": {"nums": [2, 7, 11, 15], "target": 9},
    "expected": [0, 1],
    "notes": "循环到第二个元素时，补数 2 已在哈希表中。"
  },
  {
    "name": "答案顺序颠倒",
    "args": {"nums": [3, 2, 4], "target": 6},
    "expected": [1, 2],
    "notes": "答案不在数组开头出现，需要多个元素后才找到。"
  },
  {
    "name": "相同值出现两次",
    "args": {"nums": [3, 3], "target": 6},
    "expected": [0, 1],
    "notes": "两个相同值，但索引不同。哈希表查补数时，当前值未存入，不会冲突。"
  },
  {
    "name": "负数",
    "args": {"nums": [-1, -2, -3, -4, -5], "target": -8},
    "expected": [2, 4],
    "notes": "负数也能正常用哈希表。"
  }
]
```

## 附录 C: Two Sum Solution 示例

### `solution.py`

```python
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
        return []
```

### `visual_solution.py`

```python
class Solution:
    def __init__(self, trace=None):
        self.trace = trace

    def twoSum(self, nums, target):
        seen = {}
        for i, num in enumerate(nums):
            if self.trace:
                self.trace.event(
                    event_type="array_read",
                    message=f"读取 nums[{i}] = {num}（索引 {i}，值 {num}）",
                    highlight={"objects": ["arr:nums"], "indices": {"arr:nums": [i]}},
                    before={"i": i, "num": num, "map:seen": dict(seen)},
                    pedagogy={"why_now": "遍历数组，一次只看一个元素。"}
                )
            complement = target - num
            if self.trace:
                self.trace.event(
                    event_type="hash_map_get",
                    message=f"需要补数 {complement}（因为 {num} + {complement} = {target}），检查哈希表...",
                    highlight={"objects": ["map:seen"]},
                    before={"complement": complement, "map:seen": dict(seen)},
                    pedagogy={"why_now": "查哈希表 O(1)，看补数是否存在。"}
                )
            if complement in seen:
                if self.trace:
                    self.trace.event(
                        event_type="answer_found",
                        message=f"找到了！补数 {complement} 在索引 {seen[complement]}，加上当前索引 {i} → [{seen[complement]}, {i}]",
                        highlight={"objects": ["map:seen"], "indices": {}},
                        after={"result": [seen[complement], i]},
                        pedagogy={"mental_model": "哈希表像一本快速查找的字典，key 是见过的值，value 是它的位置。"}
                    )
                return [seen[complement], i]
            seen[num] = i
            if self.trace:
                self.trace.event(
                    event_type="hash_map_put",
                    message=f"把 {num} → 索引 {i} 记录下来，以后可以快速查找",
                    highlight={"objects": ["map:seen"]},
                    before={"map:seen": dict(seen)},
                    after={"map:seen": dict(seen)},
                    pedagogy={"why_now": "当前没找到答案，先记录以便后续查找。"}
                )
        return []
```
