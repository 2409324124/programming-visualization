# Story Vision Realignment

> Written: 2026-06-26
> Status: **Direction Document — Not a Feature Spec**
> Purpose: Stop drift. Re-anchor the story animation direction before writing more code.

---

## 0. The One-Sentence Verdict

> **Current storyboard POC is useful as an experiment, but it must not become the long-term architecture.**
> **The project should pivot from trace-driven story animation to lesson-script-driven concept visualization.**

中文：当前 Story Demo 可以保留为实验，但不能继续沿着"trace → frame"的路走。
真正路线应该是"教学脚本 → 语义对象 → 动作 → 动画"。

---

## 1. 产品目标重述

### 1.1 官方重定义

> **Programming Visualization is not only an execution trace viewer.**
> **It should become a concept-first programming learning visualizer.**

它的目标不是"代码执行到哪一步"，而是：

> **学习者如何看见一个编程概念从定义到使用的全过程。**

### 1.2 具体来说

当一位学习者打开 Two Sum 的故事动画，他/她应该看到：

| 概念出现时机 | 视觉期望 |
|---|---|
| `定义一个哈希表 seen` | 一个真实的 `seen` 容器出现在画面里 |
| `seen[number] = index` | 一张规则卡出现，后续每次插入都引用这条规则 |
| `need = target - current` | 公式卡出现，`target`、`current`、`need` 三者之间有可见关系 |
| 值 `2` 被存入哈希表 | `array_item:0 → map_entry:2→0 → insert_into seen` 的动作序列 |
| 查找 `seen[2]` 成功 | `need 2` 连接到 `seen[2]`，关系可见 |

这不是"数字在框框里变来变去"。这是**概念对象参与运算和推演**。

---

## 2. 当前实现偏移点（产品审计结论）

经过对以下文件的完整阅读：

- `src/pv/storyboard.py`（458 行）
- `src/pv/render_story_html.py`（280 行）
- `problems/0001_two_sum/trace.sample.json`
- `tests/test_storyboard.py` / `tests/test_render_story_html.py`

判定结论如下：

### 2.1 `render-story` 本质是 trace viewer 的变体

**证据**：`build_storyboard()` 的第一行就是读取 `trace_data["events"]`，第一个 frame 的数据从 `events[0]` 中取 `i0 = e0["before"].get("i", 0)`。整个 11 帧的构建逻辑完全受 trace event 顺序驱动。

**问题**：trace 是执行事件，不是教学脚本。教学内容（"为什么先查后存"、"need 公式的含义"）是靠 `caption` 字符串硬塞进去的，不是视觉对象。

### 2.2 storyboard 过度依赖 `trace.sample.json`

**证据**：`storyboard.py` 顶部写明 "currently supports only 0001_two_sum"，并在第 338 行直接索引 `events[0]`、第 399 行索引 `events[3]`，完全假定 trace 结构固定。

**问题**：换一个 case（比如 `nums=[3,2,4]`），trace 的 `events[0]` 内容变了，帧编号对不上，教学文案就错了。这是不可扩展的硬编码。

### 2.3 frame schema 无法表达"定义 / 概念 / 规则 / 输入语义"

当前 frame schema：

```json
{
  "frame_id": "...",
  "step": 0,
  "title": "...",
  "caption": "...",
  "objects": [...],
  "arrows": [...],
  "badges": [...]
}
```

`objects` 列表里的元素：`array_box`、`map_entry`、`definition_card`、`rule_card`、`operation_card`、`note_card`、`label`、`complement_box`、`answer_box`。

这些对象只有 `x, y, w, h, text, state` 字段，没有：
- `semantic_type`（它是输入？定义？规则？运算结果？）
- `references`（它引用了哪条规则、哪个输入）
- `role`（在这个 frame 里它是主角还是背景）
- `action`（它是 appear / move / transform / insert_into？）

**结论**：frame 只是一帧静态截图，不是语义动作序列。

### 2.4 concept card 只是视觉标签，不是真正的语义对象

当前 `definition_card` 和 `rule_card` 是装饰性卡片，只有 `title` 和 `text` 字段。

它们**无法**：
- 被后续 frame 中的操作"引用"
- 作为 `seen[number] = index` 规则被 `map_entry` 对象"应用"
- 作为 `need = target - current` 公式被 `derive` 动作触发

在 Frame 5（`read_nums0`）和 Frame 7（`store_2_in_map`）中，`rule_card` 出现在画面里，但和 `map_entry` 的运动没有任何关联——规则卡和操作对象是相互独立的视觉元素，没有语义连接。

### 2.5 动画缺少"对象转换 / 进入容器 / 建立关系"这些核心动作

当前所有动画本质是 CSS `transform: translate(x, y)` 的位移切换。

缺少的动作：
- `transform`：`array_item` 的值转变成 `map_entry` 的 key
- `insert_into`：`map_entry` 进入 `seen` 容器
- `derive`：`target` 和 `current` 推导出 `need`
- `connect`：`need` 值连接到 `seen[need]`
- `copy`：从数组中复制一个值用于计算

### 2.6 继续做下去会变成"每题手写一堆难维护 HTML 坐标"

**证据**：
- `storyboard.py` 顶部有 21 个 layout 常量（`STAGE_W`, `ARRAY_BOX_Y`, `COMPLEMENT_X`...）
- Frame 5-10 用具体像素坐标指定每个对象位置
- 每次加一道新题，就需要新写一套坐标系、新写 N 帧硬编码

这是不可扩展的方向。Two Sum 已经是 458 行，House Robber 的 DP 表格、Permutations 的树结构会是多少行？

---

## 3. 正确的三层架构

### Layer 1: Trace / Validation Layer（已有，保留）

负责验证代码、记录真实执行事件。

```text
visual_solution.py
      ↓ (trace hooks)
harness.py
      ↓
trace.sample.json  (trace_schema.py 定义格式)
      ↓
render_text.py / render_html.py  (trace viewer)
```

已有 `harness.py` / `trace_schema.py` / `render_html.py` / `render_text.py` 都属于这一层。
这一层**不需要改动**，继续为 Layer 2 提供验证支撑即可。

### Layer 2: Lesson Script Layer（尚未存在，需要新建）

负责定义教学语义：

```text
lesson.story.json
  - 输入是什么（input_array, input_value）
  - 定义了什么概念（definition）
  - 哪些规则会被使用（rule）
  - 哪些对象如何转换（object actions: transform, derive, insert_into）
  - 为什么做这一步（goal 字段）
```

这一层的职责是**教学作者**（可以是人类，未来也可以是 LLM 辅助）来编写，而不是从 trace 自动生成。

### Layer 3: Visual Story Renderer（现有，需要重构）

负责把 lesson script 渲染成动画：

```text
lesson.story.json
      ↓ (story compiler)
frames[]  (包含 semantic actions，不是硬编码坐标)
      ↓
render_story_html.py  (只关心 frames，不关心算法逻辑)
      ↓
HTML animation
```

### 关键结论

> **Story animation should not be generated directly from trace.**
> **It should be generated from a lesson script that may reference trace events.**

"may reference" 意味着：lesson script 可以说 `"此处读取 trace event #3 的输入值"`，但不能让 trace event 直接驱动帧生成逻辑。

---

## 4. 新的 lesson script 设想

### 4.1 文件位置

```text
problems/0001_two_sum/lesson.story.json
```

这不是 trace，而是**教学脚本**。

### 4.2 草案结构

```json
{
  "lesson_id": "0001_two_sum_story",
  "problem_id": "0001_two_sum",
  "title": "Two Sum: use a hash map to remember seen numbers",
  "objects": [
    {
      "id": "input:nums",
      "type": "input_array",
      "label": "nums",
      "value": [2, 7, 11, 15]
    },
    {
      "id": "input:target",
      "type": "input_value",
      "label": "target",
      "value": 9
    },
    {
      "id": "concept:seen",
      "type": "definition",
      "label": "seen",
      "body": "保存已经见过的数字和它的下标",
      "data_structure": "hash_map"
    },
    {
      "id": "rule:seen_entry",
      "type": "rule",
      "formula": "seen[number] = index",
      "applies_to": "concept:seen"
    },
    {
      "id": "rule:need",
      "type": "rule",
      "formula": "need = target - current",
      "inputs": ["input:target", "var:current"],
      "output": "var:need"
    },
    {
      "id": "var:current",
      "type": "variable",
      "label": "current"
    },
    {
      "id": "var:need",
      "type": "variable",
      "label": "need"
    },
    {
      "id": "answer",
      "type": "answer",
      "label": "return [i, j]"
    }
  ],
  "frames": [
    {
      "id": "define_inputs",
      "goal": "看见输入",
      "actions": [
        {"action": "appear", "object": "input:nums"},
        {"action": "appear", "object": "input:target"}
      ]
    },
    {
      "id": "define_goal",
      "goal": "理解目标",
      "caption": "找到两个下标 i, j，使 nums[i] + nums[j] = target",
      "actions": [
        {"action": "appear", "object": "answer"}
      ]
    },
    {
      "id": "define_hash_map",
      "goal": "理解 seen 的作用",
      "actions": [
        {"action": "appear", "object": "concept:seen"},
        {"action": "appear", "object": "rule:seen_entry"}
      ]
    },
    {
      "id": "define_complement_rule",
      "goal": "理解补数公式",
      "actions": [
        {"action": "appear", "object": "rule:need"}
      ]
    },
    {
      "id": "read_nums0",
      "goal": "读取第一个元素",
      "trace_ref": {"event_type": "array_read", "step": 1},
      "actions": [
        {"action": "highlight", "object": "input:nums", "index": 0},
        {"action": "copy", "from": "input:nums[0]", "to": "var:current"},
        {"action": "derive", "rule": "rule:need", "result": "var:need"}
      ]
    },
    {
      "id": "check_map_fail_0",
      "goal": "查找 seen[need]，失败",
      "actions": [
        {"action": "compare", "object": "var:need", "against": "concept:seen", "result": "miss"}
      ]
    },
    {
      "id": "store_nums0",
      "goal": "按规则把当前值存入 seen",
      "actions": [
        {"action": "transform", "from": "input:nums[0]", "to": "map_entry:2_to_0"},
        {"action": "apply_rule", "rule": "rule:seen_entry"},
        {"action": "insert_into", "object": "map_entry:2_to_0", "container": "concept:seen"}
      ]
    },
    {
      "id": "read_nums1",
      "goal": "读取第二个元素",
      "trace_ref": {"event_type": "array_read", "step": 4},
      "actions": [
        {"action": "highlight", "object": "input:nums", "index": 1},
        {"action": "copy", "from": "input:nums[1]", "to": "var:current"},
        {"action": "derive", "rule": "rule:need", "result": "var:need"}
      ]
    },
    {
      "id": "check_map_success",
      "goal": "查找 seen[need]，成功！",
      "actions": [
        {"action": "compare", "object": "var:need", "against": "concept:seen", "result": "hit"},
        {"action": "connect", "from": "var:need", "to": "map_entry:2_to_0"}
      ]
    },
    {
      "id": "return_answer",
      "goal": "返回答案",
      "actions": [
        {"action": "return", "object": "answer", "value": [0, 1]}
      ]
    }
  ]
}
```

### 4.3 设计原则

- `objects` 是一等公民，在 lesson 开头声明，后续 frame 引用其 `id`
- `frames` 描述动作序列，而不是截图状态
- `trace_ref` 是可选的，用于从 trace 中读取实际值（如当前数组索引）
- `goal` 字段面向学习者，表达教学意图，不是调试信息

---

## 5. 一等公民对象类型

### 5.1 对象类型表

| type | 含义 | 示例 |
|---|---|---|
| `input_array` | 输入数组 | `nums = [2, 7, 11, 15]` |
| `input_value` | 输入标量 | `target = 9` |
| `variable` | 算法中间变量 | `current`, `need`, `i` |
| `definition` | 数据结构定义（容器） | `seen hash map` |
| `rule` | 运算规则 / 公式 | `need = target - current` |
| `operation` | 单次运算结果 | 某一步的计算 |
| `data_structure` | 具体数据结构实例 | 栈、队列、树 |
| `container` | 可以容纳其他对象的容器 | `seen`（作为动态容器） |
| `map_entry` | 哈希表中的一条记录 | `2 -> 0` |
| `array_item` | 数组中的一个元素 | `nums[0] = 2` |
| `pointer` | 指针或游标 | `left`, `right`, `i`, `j` |
| `answer` | 最终返回值 | `[0, 1]` |
| `note` | 教学注解 | "返回的是下标，不是数字" |

### 5.2 关键区分

> `definition` / `rule` / `operation` **不是装饰卡片**，而是可被后续 frame 引用的对象。

例如：
- `rule:need` 在后续 frame 中被 `derive` 动作 **apply**
- `concept:seen` 在后续 frame 中**接收** `map_entry` 的 `insert_into`
- `input:target` 参与 `rule:need` 的 **derive**
- `array_item:0`（值 2）可以 **transform** 成 `map_entry:2_to_0`

这种引用关系是当前 storyboard 完全缺失的。

---

## 6. 动作类型（Animation Actions）

### 6.1 完整动作表

| action | 含义 |
|---|---|
| `appear` | 对象出现（淡入或滑入） |
| `disappear` | 对象消失 |
| `move` | 对象从 A 位置移动到 B 位置 |
| `transform` | 对象变形为另一种类型的对象 |
| `copy` | 从一个对象复制值到另一个对象 |
| `group` | 多个对象组合成一个组 |
| `ungroup` | 组拆分为独立对象 |
| `connect` | 在两个对象之间绘制关系线 |
| `disconnect` | 移除关系线 |
| `highlight` | 突出显示对象或对象的某个部分 |
| `derive` | 基于规则从输入对象推导出新对象 |
| `insert_into` | 对象进入容器 |
| `compare` | 对象与目标对比，产生 hit 或 miss |
| `choose` | 在多个候选中选择一个（用于回溯） |
| `return` | 返回值动作（答案出现） |
| `apply_rule` | 显式标注某条规则正在被应用 |

### 6.2 关键动作解释

**`transform`**：
```text
array_item:0（值 2）-> 转变为 -> map_entry:2_to_0
视觉：方块变形，文字从 "2" 变为 "2 -> 0"
```

**`insert_into`**：
```text
map_entry:2_to_0 -> 插入 -> concept:seen 容器
视觉：map_entry 飞进 seen 容器区域
```

**`derive`**：
```text
input:target (9) + var:current (2) -> 根据 rule:need -> var:need (7)
视觉：公式卡激活，两个输入对象发出箭头指向 need
```

**`connect`**：
```text
var:need (2) -> 连接到 -> map_entry:2_to_0（在 seen 中）
视觉：need 值和 map_entry 之间出现高亮连接线
```

**`apply_rule`**：
```text
rule:seen_entry 激活高亮，操作被标注"按此规则执行"
```

---

## 7. 当前 Two Sum 应如何重做

### 7.1 不要继续在 `storyboard.py` 里硬编码 11 帧

当前路径（错误）：

```text
trace.sample.json
      ↓ (build_storyboard，直接读 events[0], events[3]...)
硬编码帧（像素坐标 + 字符串拼接）
      ↓
render_story_html.py
```

### 7.2 正确路径

```text
lesson.story.json
      ↓ (story compiler，理解 actions)
frames[]  (语义帧，不含像素坐标)
      ↓ (layout engine，自动计算位置)
render_story_html.py  (只关心渲染，不关心算法)
```

### 7.3 Two Sum 的正确教学线

```text
1.  [appear]     输入出现：nums 数组，target 值
2.  [appear]     目标定义：找两个下标 i, j，使 nums[i] + nums[j] = target
3.  [appear]     返回定义：返回 [i, j]，不是数字本身
4.  [appear]     数据结构定义：seen 容器出现（空的哈希表）
5.  [appear]     规则定义：seen[number] = index
6.  [appear]     公式定义：need = target - current
7.  [highlight]  读取 nums[0]，current = 2
8.  [derive]     target 9, current 2 -> need = 7（rule:need 激活）
9.  [compare]    need 7 vs seen -> miss（seen 是空的）
10. [transform]  nums[0] 的值 2 变成 map_entry 2_to_0
11. [apply_rule] 标注：按 seen[number] = index 规则
12. [insert_into] map_entry 2_to_0 插入 seen 容器
13. [highlight]  读取 nums[1]，current = 7
14. [derive]     target 9, current 7 -> need = 2（rule:need 激活）
15. [compare]    need 2 vs seen -> hit！seen[2] = 0
16. [connect]    need 2 连接到 map_entry 2_to_0
17. [return]     答案 [0, 1] 出现
```

---

## 8. 明确不要做的方向

```text
不要继续让 trace event 直接驱动 story 帧生成
不要继续手写每题的像素坐标
不要把 caption 字符串当主要教学载体
不要承诺学习者任意代码能自动生成 story
不要用 CSS 小修掩盖 frame schema 设计错误
不要把 story mode 和 trace viewer 混在同一个 pipeline 里
不要在 storyboard.py 里继续添加更多 frame 或 card 类型
不要把 definition_card / rule_card 当作可以继续堆砌的视觉组件
```

---

## 9. 重新规划阶段

### Phase 4.7: Story Schema Contract

**目标**：定义清晰的 lesson script 格式，不做渲染。

```text
- 新建 docs/storyboard-schema.md
- 定义 lesson.story.json 格式
- 定义 object 类型（input_array, definition, rule, variable...）
- 定义 action 类型（appear, transform, derive, insert_into...）
- 定义 frame 结构（id, goal, caption, actions）
- 写 JSON Schema 或 Pydantic model 供后续 compiler 使用
- 不做渲染，不改现有代码
```

**产出**：`docs/storyboard-schema.md` + `src/pv/lesson_schema.py`（可选）

### Phase 4.8: Lesson Compiler POC

**目标**：Two Sum lesson.story.json -> frames，替代 storyboard.py 硬编码。

```text
- 新建 problems/0001_two_sum/lesson.story.json
- 新建 src/pv/story_compiler.py
- compile(lesson) -> frames[]  (仍然只支持 Two Sum)
- 对象语义保留（id 引用，action 类型）
- layout engine：根据 object type 自动计算默认位置
- 现有 storyboard.py 保留不删，但新路径不依赖它
```

**产出**：`lesson.story.json` + `story_compiler.py`（不改 render_story_html.py）

### Phase 4.9: Renderer Cleanup

**目标**：render_story_html.py 只关心 frames，不关心算法逻辑。

```text
- render_story_html.py 接受新 frame 格式（带 actions）
- 支持 appear, move, transform, connect, derive 的基础渲染
- 不再需要 storyboard.py 注入的硬编码对象
- 更新 tests/test_render_story_html.py 覆盖新 action 类型
```

**产出**：重构后的 `render_story_html.py`

### Phase 5.0: Rebuild Two Sum Story Properly

**目标**：从 lesson.story.json 生成完整 Two Sum 故事 HTML。

```text
- 定义、规则、输入、运算对象真正参与动画
- transform 动作可见（array_item -> map_entry）
- derive 动作可见（公式激活）
- insert_into 动作可见（进入容器）
- connect 动作可见（关系线）
- 不依赖 trace.sample.json 驱动帧顺序
```

**产出**：新版 `examples/story_0001_two_sum.case0.html`

---

## 10. 最终判断

### 10.1 技术判断

| 问题 | 结论 |
|---|---|
| `render-story` 是否只是 trace viewer 变体？ | **是。** 它读 trace events，硬编码了 events 的索引位置。 |
| storyboard 是否过度依赖 trace？ | **是。** 换一个 test case 就会出错。 |
| frame schema 能否表达教学语义？ | **否。** 只有坐标+状态，没有 action 类型，没有对象引用。 |
| concept card 是否是真正的语义对象？ | **否。** 纯视觉装饰，不参与 frame 间的逻辑关系。 |
| 动画是否有"对象转换/进入容器"？ | **否。** 只有 CSS translate 位移，没有 transform/insert_into/derive。 |
| 继续做会不会变成手写坐标地狱？ | **会。** 已经有 21 个 layout 常量，House Robber 需要 DP 表格，更难。 |

### 10.2 架构判断

```text
当前架构（应当停止继续扩展）：
  trace.sample.json
        ↓
  build_storyboard()  <-- 硬编码帧、硬编码坐标、硬编码事件索引
        ↓
  render_story_html.py

正确架构（应当建立）：
  lesson.story.json  <-- 教学作者编写，定义对象和动作
        ↓
  story_compiler.py  <-- 理解 actions，计算布局
        ↓
  frames[]  <-- 语义帧
        ↓
  render_story_html.py  <-- 纯渲染，不含业务逻辑
```

### 10.3 中文总结

当前 Story Demo 证明了这个视觉方向**可行**，但也暴露了它在 schema 设计上的根本缺陷。

继续往 `storyboard.py` 里加帧，只会让问题更深、更难改。

**正确的下一步是：先写 schema，再写 compiler，最后重建渲染器。不要在错误的基础上继续堆功能。**

---

## 附录：README 建议补充

在 README.md 的 `render-story` 描述处（当前第 78 行）之后，建议添加：

```text
> Warning: The current story demo is experimental.
> The long-term direction is lesson-script-driven concept visualization,
> not trace-driven animation. See docs/story-vision-realignment.md.
```
