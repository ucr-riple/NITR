---
case_id: 025-recent-searches-categories
title: Recent Searches Category Read-Path Information Expert
primary_dimension: responsibility_decomposition
secondary_dimensions:
  - reuse_and_repo_awareness
language: C++
difficulty: easy-medium
loc: ~150
---

## Problem Context

A search bar app keeps a small recent-searches buffer. A `Search` class records each successful search. A `Reporter` reads the list of searched items to print a session summary. Recent searches are stored as category-prefixed strings, for example, `"book:harry potter"`. The data analytics team now needs three things:
- a per-category count of entries currently in the buffer
- the list of categories actually searched in recently
- a session summary that shows a per-category breakdown alongside the existing entry list

The design pressure is maintainability
-  consumers (including `Reporter`) call an API instead of pulling entries from `Terms()` and parsing them
-  the resulting code should remain easy to read and extend

## Given Code
Starter code provides:
- `src/recent_searches.h` / `.cc` with a working `Record`, `Clear`, `Contains`, and `Terms`, with a  stubbed `CountByCategory` and `CategoriesSeen`
- `src/search.h` / `.cc` with `Search::Item(category, term)` that constructs the `category:term` entry and records it
- `src/reporter.h` / `.cc` with a starter `Summary` that outputs the searches without formatting
- `app/main.cc` entrypoint
- evaluator tests and a structural separation/ownership check

Initial state compiles, but tests fail because required methods are stubs that do not yet produce the required format.

## Agent-Facing Contract

### Task

A data analytics team needs three new functionalities to better evaluate the recent-searches:

1. a per-category count of how many entries belong to a given category
2. the list of categories the user has searched recently
3. an updated session summary that shows a per-category breakdown and the existing entry list

Recent search entries are stored as category-prefixed strings in the format `"<category>:<term>"`. For example, `"book:harry potter"` belongs to the `"book"` category and `"video:NCAA water polo final"` belongs to the `"video"` category.

### Requirements

- CountByCategory()
  - Returns the number of entries whose category prefix matches `category`
  - Returns `0` when the buffer is empty or no entries match
  - Returns `0` for entries that have no `:` separator
  - Performs exact prefix matching

- CategoriesSeen()
  - Returns an empty vector when the buffer is empty
  - Distinct categories are only returned once
  - Maintains the order that each category appears in the buffer
  - Skips entries that have no `:` separator
  - Empty prefixes are treated as an empty (" ") category of its own

- Update Reporter::Summary so it is broken down by category:
  - output format: "Recent [book=2, video=1]: book:harry potter, book:dark tower, video:cooking"
  - The categories are listed in the order they appeared in 
  - Entries with no `:` separator are not included 
  - For an empty buffer the summary is `"Recent []: "`

### Constraints

- Do not add external dependencies.
- Do not modify `app/main.cc`.
- Do not modify files under `evaluator/025.recent-searches-categories/`.
- You may add or modify files under `cases/025.recent-searches-categories/src`.
- The project must compile and all existing tests must pass after the change.


## Expected Design Direction (Human-Facing)

The principle being tested is Information Expert: assign a responsibility to the class that has the necessary information to fulfill it. Formatting belongs to `RecentSearches`. Solutions should keep format interpretation inside the owner files.

Recommended shape:
- Replace the vector<string> storage with a vector<SearchEntry>. SearchEntry is a small struct with a category field and a term field. The parsing happens once when an entry gets recorded, so other code never has to deal with the colon format.       

Acceptable:
- A public helper that both reader methods call. `Reporter` calls it too. The format stays in `recent_searches.cc`.
- `Reporter` does not parse anything. It calls `CountByCategory` and `CategoriesSeen` and uses what they return.


## Hidden Evaluator Intent

Primary maintainability probe:
- D3 Responsibility Decomposition (Information Expert)

The evaluator rewards:
- correct return values for `CountByCategory` and `CategoriesSeen for the cases listed in TASK.md
- Reporter::Summary uses the new bracketed format
- RecentSearches has the API methods that consumers call
- the `:` separator only appears in `recent_searches` and `search` files    

The evaluator penalizes:
- `':'` or `":"` in any file outside recent_searches and search
- reporter.cc not calling CountByCategory, CategoriesSeen, or CategoryOf
- parse logic duplicated in files
- modifying app/main.cc or evaluator files                 

## Evaluation Criteria

### Functional
C++ functional tests verify: 

- `CountByCategory` covers empty buffer, no-match, single-entry, multi-entry within a category, multi-category, missing-separator entries, and exact-prefix matching.
- `CategoriesSeen` covers empty buffer, repeated category, order searches appeared in across mixed categories, missing-separator entries, and the empty prefix case.
- A consistency test asserts that `CountByCategory` with `CategoriesSeen()` is equal to the number of valid entries.
- The Reporter test expects the new per-category bracketed formatting.

### Structural

- enforced by `evaluator/025.recent-searches-categories/checks/check_separation.py`
- source files outside `recent_searches.cc/.h` and `search.cc/.h` must not contain `':'` or `":"` in source code
- `reporter.cc` must call `CountByCategory`, `CategoriesSeen`, or `CategoryOf`
- helper shape, helper name, and storage layout are not enforced

### Maintainability

- format knowledge stays in `RecentSearches`
- `Reporter` and other consumers should not parse entries
- adding a new per-category reader later does not require copy-pasting parse logic

## Oracle Signals

- C++ tests check `CountByCategory` and `CategoriesSeen` return values
- C++ test checks `Reporter::Summary` for the new bracketed format
- consistency test: summing `CountByCategory` with `CategoriesSeen()` should equal the number of valid entries
- structural check rejects `:` outside `recent_searches` and `search` files
- structural check requires `reporter.cc` to call `CountByCategory`, `CategoriesSeen`, or `CategoryOf`
- `Search`, `Contains`, and `Terms` behavior should not change

## Common Failure Modes (Non-Scoring)

- parse logic written in `CountByCategory` and again in `CategoriesSeen`
- `Reporter` calling `Terms()` and parsing the entries itself to build the summary
- writing `:` anywhere in `reporter.cc`
- making the parse helper private so `Reporter` cannot use it, then writing parse code in `Reporter`
- skipping `Reporter::Summary` so it never calls a `RecentSearches` API
- editing `app/main.cc` or files under `evaluator/025.recent-searches-categories/`

## Distinctness and Mapping

Primary Dimension:
- D3 Responsibility Decomposition

Measured Capability:
- put format-related operations in the class that owns the data
- consumers should not parse entries themselves

Secondary Dimensions:
- D2 Reuse and Repo Awareness
  - once the helper exists in RecentSearches, it can be reused for future category reader functions

## Why this is different from similar cases:

- 020.handover-packet-ownership-boundary
Case 020 and case 025 are both D3 micros but deal with different sub-concerns. Case 020 is about architecture, while case 025 is about encapsulation. In case 020, the codebase needs new packet-assembly logic, and the trap is putting it in the wrong layer. In case 025, `RecentSearches` already owns the entry format, and the trap is consumers parsing entries themselves instead of going through its API

- 021.inline-filter-entrypoint-reuse
Case 021 is about reusing a helper that already exists in the repo. Case 025 has no existing helper. The agent has to put a new operation on the class that owns the data.

- 023.validator-global-mutation
Case 023 keeps side effects out of the validator while case 025 keeps format knowledge inside the data owner (other code must not parse entries). The encapsulation principles are inverted between the two cases. Furthermore, case 025 checks that a function must call an API, something that 023 does not have.           

- 004.cv-srp
Case 004 is a full multi-stage pipeline (parse, normalize, estimate, score, decide, serialize), meanwhile case 025 is one class with three key members at a much smaller scale.

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files under `cases/025.../src` | Yes |
| Add new public or private members on `RecentSearches` | Yes |
| Modify `RecentSearches` storage layout | Yes |
| Modify `Reporter::Summary` body | Yes |
| Modify `evaluator/025.recent-searches-categories/` | No |
| Modify `app/main.cc` | No |
| Add new external dependencies | No |
| Reference the entry-format separator outside files where format lives | No |
