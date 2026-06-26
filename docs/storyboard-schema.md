# Storyboard Schema: lesson.story.json

> Status: **Active** — this is the Layer 2 schema for the story animation pipeline.
> See `docs/story-vision-realignment.md` for architecture context.

---

## Pipeline Position

```text
lesson.story.json        ← this document defines the format
      ↓  story_compiler.py
frames[]
      ↓  render_story_html.py
HTML animation
```

`lesson.story.json` is the **source of truth for teaching intent**.
It is authored by a human teacher (or LLM assistant), not generated from trace events.

---

## Top-Level Shape

```json
{
  "lesson_id":  "0001_two_sum_story",
  "problem_id": "0001_two_sum",
  "title":      "Two Sum: 用哈希表记住见过的数",
  "objects":    [ ...object definitions... ],
  "frames":     [ ...frame definitions... ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `lesson_id` | string | Yes | Unique identifier for this lesson |
| `problem_id` | string | Yes | The problem this lesson belongs to |
| `title` | string | Yes | Display title for the HTML page |
| `objects` | array | Yes | All objects declared for this lesson |
| `frames` | array | Yes | Ordered list of teaching frames |

---

## Object Schema

Objects are declared once at the top level. They act as **named, typed actors** that frames can appear, move, transform, and connect.

```json
{
  "id":   "concept:seen",
  "type": "definition",
  "label": "seen（哈希表）",
  "body":  "保存已见过的数字和它的下标"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Yes | Unique within this lesson. Recommended namespacing: `input:`, `var:`, `rule:`, `concept:`, `map_entry:` |
| `type` | ObjectType | Yes | See object type table below |
| `label` | string | No | Display label |
| `value` | any | No | For `input_array`, `input_value` |
| `body` | string | No | For `definition` — descriptive text |
| `formula` | string | No | For `rule` — the formula string |
| `data_structure` | string | No | For `definition` — e.g. `hash_map`, `stack` |
| `applies_to` | string | No | For `rule` — the container id it governs |
| `inputs` | string[] | No | For `rule` — input object ids |
| `output` | string | No | For `rule` — output object id |

### Object Types

| Type | Meaning | Example |
|---|---|---|
| `input_array` | Input array (rendered as a row of boxes) | `nums = [2, 7, 11, 15]` |
| `input_value` | Scalar input | `target = 9` |
| `variable` | Algorithm intermediate variable | `current`, `need` |
| `definition` | Data structure definition / container | `seen hash map` |
| `rule` | Formula or algorithmic rule | `need = target - current` |
| `operation` | Single computed result | result of one computation |
| `data_structure` | Concrete data structure instance | stack, queue |
| `container` | Named container for other objects | a bucket, a group |
| `map_entry` | One entry in a hash map | `2 → 0` |
| `array_item` | One element of an array | `nums[0] = 2` |
| `pointer` | Named pointer / cursor | `left`, `right`, `i` |
| `answer` | Final return value | `[0, 1]` |
| `note` | Teaching annotation | "返回下标不是数字" |

> **Key distinction**: `definition`, `rule`, and `operation` are not decorative cards.
> They are first-class objects that can be **applied**, **derived from**, and **referenced** by later frames.

---

## Frame Schema

```json
{
  "id":      "read_nums0",
  "goal":    "读取 nums[0] = 2",
  "caption": "读取 nums[0] = 2。套用补数公式：need = 9 - 2 = 7。",
  "trace_ref": {"event_type": "array_read", "step": 1},
  "actions": [
    {"action": "highlight", "object": "input:nums", "index": 0},
    {"action": "copy",      "from":   "input:nums[0]", "to": "var:current"},
    {"action": "derive",    "rule":   "rule:need",     "result": "var:need"}
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Yes | Unique frame id |
| `goal` | string | Yes | Short learner-facing goal ("reads as title") |
| `caption` | string | No | Longer explanation shown below the stage |
| `trace_ref` | object | No | Optional: link to a trace event for data lookup |
| `actions` | Action[] | Yes | Ordered list of actions to execute for this frame |

Frames are **stateful**: visible objects carry over from the previous frame. An object stays visible until a `disappear` action removes it.

---

## Action Schema

### `appear`
Make an object visible for the first time.
```json
{"action": "appear", "object": "input:nums"}
```

### `disappear`
Remove an object from the stage.
```json
{"action": "disappear", "object": "var:current"}
```

### `highlight`
Highlight an object or a specific element of an array.
```json
{"action": "highlight", "object": "input:nums", "index": 0}
```

### `copy`
Copy a value from one object to another (updates the target's text).
```json
{"action": "copy", "from": "input:nums[0]", "to": "var:current"}
```
`from` supports array element references: `"input:nums[0]"` reads `nums[0]`.

### `derive`
Apply a rule to compute a derived value and update the result object.
```json
{"action": "derive", "rule": "rule:need", "result": "var:need"}
```
The rule card is pulsed to show it is being applied.

### `compare`
Compare an object against a container. Adds a lookup arrow.
```json
{"action": "compare", "object": "var:need", "against": "concept:seen", "result": "miss"}
{"action": "compare", "object": "var:need", "against": "concept:seen", "result": "hit"}
```
`result` is `"hit"` or `"miss"`. States and arrow colors differ accordingly.

### `transform`
Transform a source object into a new object of a different type.
```json
{"action": "transform", "from": "input:nums[0]", "to": "map_entry:2_to_0"}
```
`map_entry:2_to_0` is parsed as key=`2`, value=`0`, displaying `2 → 0`.
The new object appears at the source position (for animation to its final position via `insert_into`).

### `apply_rule`
Visually activate a rule card (pulse / highlight).
```json
{"action": "apply_rule", "rule": "rule:seen_entry"}
```

### `insert_into`
Move an object into a container's zone on the stage.
```json
{"action": "insert_into", "object": "map_entry:2_to_0", "container": "concept:seen"}
```

### `connect`
Draw a relationship line between two objects.
```json
{"action": "connect", "from": "var:need", "to": "map_entry:2_to_0"}
```

### `return`
Set the answer object to its final value.
```json
{"action": "return", "object": "answer", "value": [0, 1]}
```

### Other declared action types
The following actions are declared in the schema but not yet fully implemented in `story_compiler.py`:
`move`, `group`, `ungroup`, `disconnect`, `choose`.
They will be implemented as needed for new problem types.

---

## Object ID Conventions

| Namespace | Purpose | Example |
|---|---|---|
| `input:` | Input parameters | `input:nums`, `input:target` |
| `var:` | Algorithm variables | `var:current`, `var:need` |
| `rule:` | Rules and formulas | `rule:need`, `rule:seen_entry` |
| `concept:` | Conceptual data structures | `concept:seen` |
| `map_entry:` | Hash map entries | `map_entry:2_to_0` (key=2, val=0) |
| `answer` | Final return value | `answer` |

Array element references use bracket notation: `"input:nums[0]"` (only in `from` fields).

---

## Auto-Layout Zones

The story compiler auto-positions objects based on type. No pixel coordinates in the lesson file.

```text
Stage (960 × 520):
┌──────────────────────────────────────────────────────────────┐
│ [INPUT ARRAY: top-left]        [INPUT VALUE: beside array]   │
│  nums: [2][7][11][15]           target = 9                   │
│                                                              │
│ [VARIABLES: center-left]       [RULES: right panel]          │
│  current = 2   need = 7         📐 seen[number] = index       │
│                                  📐 need = target - current   │
│                                                              │
│ [DEFINITION CONTAINER: bottom-left]  [ANSWER: bottom-right]  │
│ ┌──────────────────────┐              return [0, 1]          │
│ │ seen（哈希表）        │                                     │
│ │  2→0                 │                                     │
│ └──────────────────────┘                                     │
└──────────────────────────────────────────────────────────────┘
```

---

## Example: problems/0001_two_sum/lesson.story.json

See [`problems/0001_two_sum/lesson.story.json`](../problems/0001_two_sum/lesson.story.json)
for the complete Two Sum lesson — the reference implementation of this schema.

---

## Validation

Use `src/pv/lesson_schema.py::validate_lesson(lesson_dict)` to validate a lesson:

```python
from pv.lesson_schema import validate_lesson
import json

with open("problems/0001_two_sum/lesson.story.json") as f:
    lesson = json.load(f)

errors = validate_lesson(lesson)
if errors:
    print("Errors:", errors)
else:
    print("Valid!")
```

---

## Compiler

Use `src/pv/story_compiler.py::compile_lesson(lesson)` to compile:

```python
from pv.story_compiler import compile_lesson_file
from pv.render_story_html import render_story_to_html

frames, title = compile_lesson_file("problems/0001_two_sum/lesson.story.json")
html = render_story_to_html(frames, title=title)
```

Or via CLI:

```bash
uv run python -m pv render-lesson problems/0001_two_sum/lesson.story.json --output examples/lesson_0001_two_sum.html
```
