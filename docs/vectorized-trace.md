# Vectorized Trace — Design Notes

> 状态：前瞻设计文档，当前版本 **未实现**。默认拒绝 numpy 等第三方依赖。
> 本文档为未来向量化代码可视化提供技术路线，不作为当前开发任务。

## 1. 问题

当前 trace 体系基于逐行 Python 循环：

```python
for i in range(len(nums)):
    seen[nums[i]] = i   # trace.event("hash_map_put", ...)
```

每个语义步骤对应一个 `trace.event()` 调用。这对 `class Solution` 的 LeetCode 风格循环代码
工作良好。

但学习者可能写出向量化代码：

```python
def twoSum(self, nums, target):
    a = np.array(nums)
    diff = target - a
    mask = np.isin(diff, a)
    ...
```

这里没有显式循环，也就没有地方插入 `trace.event()`。传统逐行 trace 无法表达
"对整个数组同时做减法"这种批量操作。

## 2. 结论：向量化不是不能可视化

它需要的不是循环 trace，而是 **操作图（operation graph）trace**。

类比：深度学习框架（TensorFlow、PyTorch）本身就用计算图来表示批量操作。
NumPy 通过 `__array_ufunc__` 和 `__array_function__` 协议暴露了类似的拦截点。

| 逐行 trace | 向量化 trace |
|-----------|-------------|
| 事件：pointer_move, array_read | 事件：ufunc_call, broadcast, reduce |
| 状态：prev, curr, best | 状态：shape, dtype, 中间数组快照 |
| 渲染：一步步动图 | 渲染：操作节点 + 数据流箭头 + 形状标注 |

## 3. NumPy 拦截机制（技术参考）

NumPy 从 1.13 开始提供两个协议：

### `__array_ufunc__`

拦截 ufunc 调用（`+`, `*`, `np.sin`, `np.maximum` 等）：

```python
class TraceArray:
    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        # 记录：ufunc.__name__, inputs, output shape
        trace.event("ufunc_call", ...)
        # 委托给真正的 numpy 数组
        raw_inputs = [x._raw if isinstance(x, TraceArray) else x for x in inputs]
        result = getattr(ufunc, method)(*raw_inputs, **kwargs)
        return TraceArray(result, trace)
```

### `__array_function__`

拦截命名空间函数（`np.sum`, `np.where`, `np.sort` 等）：

```python
def __array_function__(self, func, types, args, kwargs):
    trace.event("array_func", func_name=func.__name__, ...)
    raw_args = [x._raw if isinstance(x, TraceArray) else x for x in args]
    return func(*raw_args, **kwargs)
```

## 4. 当前立场

**默认拒绝 numpy。** `submission_policy.py` 将 `numpy` 列入 `UNSUPPORTED`，
学习者提交含 `import numpy` 的代码时得到中文错误：

> 不支持的依赖 numpy。本工具只使用 Python 标准库，不安装第三方数据处理库。请用纯 Python 实现算法。

这是合理的：在 trace 体系能处理向量化代码之前，允许 numpy 只会产生
"运行通过但无 trace" 的结果，对学习者帮助有限。

## 5. 未来路线

### Phase A：`--allow-third-party numpy`

- 新增 CLI flag，跳过 `numpy` 的 import 拦截
- 此时代码可运行并通过输出验证
- trace_mode 为 `validation_only`（无语义事件）
- 不实现 TraceArray

### Phase B：`--trace-numpy`

- 实现 `TraceArray` wrapper
- 拦截 ufunc 和 array_function 调用
- 生成操作图 trace（与现有语义 trace 不同格式）
- 新增 `render_html` 的 tensor/array 操作图渲染

### POC 阶段建议覆盖的函数

| 类别 | 函数 |
|------|------|
| 构造 | `np.array`, `np.asarray`, `np.zeros`, `np.ones` |
| ufunc | `+`, `-`, `*`, `/`, `<`, `>`, `==`, `np.maximum`, `np.minimum` |
| 比较/布尔 | `np.isin`, boolean mask indexing |
| 条件 | `np.where` |
| 聚合 | `np.sum`, `np.max`, `np.argmax` |
| 排序 | `np.sort`, `np.argsort` |
| 累积 | `np.cumsum` |

这些覆盖了 LeetCode 风格题目中最常见的向量化操作：
prefix sum、sliding window max、二分搜索的向量化变体、直方图、计数等。

## 6. Trace 事件草案（Phase B 实现时参考）

```json
{
  "event_type": "ufunc_call",
  "func": "subtract",
  "inputs": [{"name": "a", "shape": [4], "dtype": "int64"}],
  "output": {"shape": [4], "dtype": "int64"},
  "message": "计算 target - nums：对每个元素做 9 - value"
}
```

```json
{
  "event_type": "array_func",
  "func": "isin",
  "description": "np.isin(diff, a)",
  "inputs": [{"shape": [4]}, {"shape": [4]}],
  "output": {"shape": [4], "dtype": "bool"},
  "message": "检查 diff 中的每个元素是否出现在 nums 中"
}
```

## 7. 渲染草案（Phase B 实现时参考）

HTML 渲染器中对操作图的展示：

- **操作节点**：圆角矩形，显示操作名（subtract, isin, where）
- **数据流箭头**：从输入节点指向操作节点，从操作节点指向输出
- **形状标注**：(4,) → subtract → (4,)
- **悬停高亮**：hover 操作节点时，对应数据流高亮
- **非数值数组**：可折叠，显示前 5 个元素 + "... (共 N 个)"

## 8. 不在此设计范围内

- GPU / CUDA trace
- JAX / PyTorch / TensorFlow
- 自动微分 / 梯度 trace
- 分布式数组
- 稀疏矩阵
- Pandas DataFrame 操作

这些都是超出 LeetCode 风格算法学习范围的工程复杂度。

## 9. 与现有 trace 体系的关系

向量化 trace 是现有 `TraceBuilder` 体系的扩展，不是替代：

```text
普通循环代码 → TraceBuilder.event() → semantic trace JSON → render
向量化代码   → TraceArray.__array_ufunc__() → op-graph trace JSON → render (future)
```

两种 trace 可以共存于同一个 trace envelope，用 `trace_format` 字段区分：
- `"trace_format": "semantic"` — 现有逐事件 trace
- `"trace_format": "op_graph"` — 未来操作图 trace

渲染器根据 `trace_format` 选择渲染路径。

## 10. 总结

向量化代码的可视化不是技术不可能，而是需要不同的 trace 模型。
当前阶段（Phase 3.5）选择明确拒绝 numpy，给出清晰的中文错误提示，
同时保留未来通过 `--allow-third-party` / `--trace-numpy` 逐步开放的路线。

**当前不做任何实现。** 本文档仅供未来参考。
