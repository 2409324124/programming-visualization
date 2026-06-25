# Legal and Licensing Notes

This document is a practical engineering guideline, not legal advice.

## 1. Project Positioning

This repository should position itself as:

> An original programming visualization tool for LeetCode-style interview problem patterns.

It should not position itself as:

- a LeetCode clone;
- a LeetCode mirror;
- an official LeetCode companion;
- a scraper of LeetCode content;
- a redistribution of LeetCode problem statements or editorials.

## 2. Main Legal Boundary

The project may discuss common interview problem patterns, but should not copy protected platform content.

Avoid copying:

- official problem descriptions;
- official examples;
- official test cases;
- official editorials;
- official diagrams;
- official screenshots;
- premium content;
- crawled metadata or scraped content.

Instead, create:

- original short summaries;
- original input/output descriptions;
- original educational examples;
- original local test cases;
- original diagrams and explanations;
- original trace messages.

## 3. Naming and Branding

Recommended repository name:

```text
programming-visualization
```

Avoid names that imply official affiliation, such as:

```text
leetcode-visualizer-official
leetcode-hot100-clone
leetcode-judge
```

It is acceptable to use descriptive language such as:

```text
LeetCode-style interview problems
classic Hot 100 style patterns
inspired by common interview problem patterns
```

But the project should include a non-affiliation statement:

```text
This project is not affiliated with, endorsed by, or sponsored by LeetCode.
Problem summaries, examples, tests, explanations, and visualizations in this repository are original educational content.
```

## 4. Problem Mapping Strategy

Use internal educational IDs as the primary identity.

Recommended:

```text
0001_hash_complement_lookup
0011_two_pointer_area_scan
0206_linked_list_reversal
```

Optional metadata can include a reference mapping:

```json
{
  "reference": {
    "platform": "LeetCode",
    "id": 1,
    "title": "Two Sum",
    "usage": "compatibility reference only"
  }
}
```

The public lesson page should emphasize the original learning title, not the external platform identity.

## 5. Test Cases

All test cases should be written by this project.

Do not copy official examples or hidden tests.

Good educational case:

```json
{
  "name": "answer appears after one previous value",
  "args": {"nums": [2, 7, 11, 15], "target": 9},
  "expected": [0, 1],
  "notes": "This case demonstrates complement lookup with a single previous value."
}
```

Even when a tiny example happens to look like a widely known example, prefer writing it for a specific teaching purpose and do not copy the surrounding problem text.

## 6. Source Code Reuse

Do not copy code from projects without checking their licenses.

Public GitHub repository visibility does not automatically mean open-source reuse permission.

Safe categories to study or reuse, subject to license text:

- MIT
- Apache-2.0
- BSD-style permissive licenses

Be careful with:

- GPLv3 or other copyleft licenses if the goal is a permissive repository;
- projects with no license;
- commercial learning platforms;
- sites with terms that restrict copying, scraping, or redistribution.

## 7. Recommended Project License

For this repository:

- code: MIT or Apache-2.0;
- original docs and diagrams: CC BY 4.0 if separated from code;
- if keeping it simple at the beginning: use one clear permissive license for the whole repo.

MIT is simpler. Apache-2.0 provides explicit patent language.

## 8. Scraping Policy

Do not write or include scrapers for LeetCode or similar commercial platforms.

Do not automate collection of:

- problem statements;
- examples;
- submissions;
- editorial content;
- paid content;
- discussion content.

Use manually written original curriculum content.

## 9. README Disclaimer

Add a disclaimer similar to:

```text
This project is an independent educational tool for visualizing common programming interview problem patterns. It is not affiliated with, endorsed by, or sponsored by LeetCode. All lesson summaries, examples, test cases, explanations, traces, and visual assets in this repository are original unless otherwise stated.
```

## 10. Practical Review Checklist

Before adding a new problem folder, check:

- [ ] Is the lesson summary original?
- [ ] Are the examples original?
- [ ] Are test cases original?
- [ ] Are diagrams original?
- [ ] Is any external code license-compatible?
- [ ] Does the problem metadata avoid implying official affiliation?
- [ ] Does the page focus on learning pattern, not platform branding?
