# Online Judge Notes

This project should understand online judge mechanics, but it should not become a production online judge in the MVP.

## 1. What a Production Online Judge Usually Does

A typical online judge pipeline is:

```text
receive submission
        ↓
compile if needed
        ↓
run on each test case in sandbox
        ↓
collect stdout / return value / runtime / memory
        ↓
compare with expected output or custom checker
        ↓
aggregate verdict
```

Common verdicts include:

- Accepted;
- Wrong Answer;
- Runtime Error;
- Time Limit Exceeded;
- Memory Limit Exceeded;
- Compile Error;
- Presentation Error in some systems;
- System Error or Judge Error.

## 2. Why This Project Should Not Start There

A production judge solves different problems:

- safely running arbitrary untrusted code;
- limiting CPU, memory, wall time, and file/network access;
- supporting many languages;
- scheduling submissions;
- hiding tests;
- ensuring fairness;
- preventing abuse.

This project solves a different problem:

> Make algorithm execution understandable for learners.

So the MVP should be a local educational validator, not a public sandbox.

## 3. Educational Validator Scope

The local validator should:

- run only curated problem folders;
- run small visible cases;
- call a known Python `Solution` method;
- compare result with expected output or a custom checker;
- record trace events;
- show the trace even when the result is wrong;
- classify common errors when possible.

It does not need:

- hidden tests;
- account system;
- code queue;
- multi-language support;
- public arbitrary-code execution;
- heavy sandboxing for v1.

## 4. LeetCode-Style Method Contract

Many Python interview problems use a pattern like:

```python
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        ...
```

The local harness should support:

- importing `Solution` from a file;
- selecting method name from metadata;
- loading args from `cases.json`;
- passing args by keyword or configured order;
- converting special structures;
- normalizing output;
- checking expected output.

## 5. Data Structure Serialization

The validator should support common educational structures:

### Arrays

```json
[1, 2, 3]
```

### Linked Lists

```json
{"kind": "linked_list", "values": [1, 2, 3]}
```

Optional cycle metadata:

```json
{"kind": "linked_list", "values": [3, 2, 0, -4], "cycle_pos": 1}
```

### Binary Trees

Use level-order lists:

```json
[3, 9, 20, null, null, 15, 7]
```

### Grids

```json
[["1", "1", "0"], ["0", "1", "0"]]
```

## 6. Multiple Valid Answers

Some problems have multiple valid outputs.

Do not always use raw equality. Add optional checkers.

Examples:

- permutations: compare sorted normalized collections;
- 3Sum: compare set of sorted triples;
- graph traversal: compare acceptable structure rather than exact traversal if order is not required;
- floating-point problems: compare tolerance if ever needed.

Problem metadata can include:

```json
{
  "checker": "unordered_triplets"
}
```

## 7. Error Classification for Learning

The educational validator should classify failures in beginner-friendly terms.

Useful categories:

- wrong output;
- exception;
- step limit exceeded;
- possible infinite loop;
- invalid linked-list structure;
- state leakage between cases;
- mutation of input when mutation is not expected;
- output shape mismatch.

Example message:

```text
The result is correct for the first case, but the second case starts with a non-empty class-level cache. This looks like state leakage between test cases.
```

## 8. Step Limit

Even without production sandboxing, the MVP should have a simple step/event limit.

Recommended default:

```text
max_events = 10_000
```

When exceeded:

```text
Trace stopped because more than 10,000 events were emitted. This may indicate an infinite loop or an overly detailed trace hook.
```

## 9. Future Sandbox Boundary

If this project ever runs arbitrary code from unknown users on a server, it must add a real sandbox or delegate execution to a proven sandboxed judge system.

Future requirements would include:

- container or microVM isolation;
- network disabled by default;
- filesystem restrictions;
- CPU/memory/wall-time limits;
- process limits;
- output size limits;
- queue worker model;
- audit logging.

This is explicitly not part of MVP.

## 10. Practical MVP Decision

For now:

```text
curated Python reference solutions
+ local visible test cases
+ deterministic trace
+ educational checker
```

This is enough to prove the product idea without taking on online judge security complexity too early.
