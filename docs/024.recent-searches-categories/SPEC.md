---
case_id: 024-recent-searches-categories
title: Recent Searches Category Count Separation
primary_dimension: responsibility_decomposition
secondary_dimensions:
  - reuse_and_repo_awareness
language: C++
difficulty: easy-medium
loc: ~150
---

## Problem Context
A search bar app keeps a small recent-searches buffer. A `Search` class records each successful search. A `Reporter` reads the list of searched items to print a summary at the end of a session.

Recent search entries are stored as category-prefixed strings. For example, searching for `"harry potter"` under the `"book"` category is stored as the string `"book:harry potter"`. 

The data tracker now needs to count the amount of searches, per-category.

The design pressure is maintainability:
- two responsibilities (increasing count and extracting category) should not be done inside one method
- the resulting code should remain easy to read and extend

## Given Code
Starter code provides:
- `src/recent_searches.h` / `.cc` with a working `Contains`, a `Terms` accessor, and a stubbed `CountByCategory`
- `src/search.h` / `.cc` with `Search::Item(category, search_word)` that constructs a `"category:term"` entry and records it
- `src/reporter.h` / `.cc` that creates a summary output
- `app/main.cc` entrypoint 
- evaluator tests and a structural separation check

Initial state compiles, but tests fail because `RecentSearches::CountByCategory` is currently a stub returning `0`.

## Agent-Facing Contract 

### Task

An analytics team needs a per-category count of recent searches. Complete the existing `RecentSearches` class by implementing a method named `CountByCategory` that accepts a category and returns how many entries in recent-searches belong to that category.

Recent search entries are stored as category-prefixed strings in the format `"<category>:<term>"`. For example, `"book:harry potter"` belongs to the `"book"` category and `"video:NCAA water polo final"` belongs to the `"video"` category.

### Requirements

- Return the number of entries whose category prefix matches `category`
- Return `0` if no entries match
- Return `0` if the buffer is empty
- An entry without a `:` separator should not be counted

### Constraints

- Do not add external dependencies.
- Do not modify `app/main.cc`.
- Do not modify files under `evaluator/024.recent-searches-categories/`.
- You may add or modify files under `cases/024.recent-searches-categories/src`.
- The project must compile and all existing tests must pass after the change.

## Expected Design Direction (Human-Facing)
`CountByCategory` has two jobs: pulling the category out of a search string, and counting how many entries match a given category. These are two separate jobs and should live in two separate places.

Recommended shape:
- one helper method that takes a search entry and returns its category prefix
- `CountByCategory` only loops over entries and compares categories — no string parsing inside it

Acceptable approaches include:
- a private member method `std::string CategoryOf(const std::string&)` on `RecentSearches`
- a free helper function in `recent_searches.cc` that does the same job

The exact name and location of the helper do not matter, only that the category-extraction logic does not live inside `CountByCategory`.

## Hidden Evaluator Intent
Primary maintainability probe:
- D3 Responsibility Decomposition

The evaluator rewards:
- correct counts for different prefixed search edge cases
- a `CountByCategory` function that does not have string parsing logic
- a separate helper that deals with category extraction/string parsing

The evaluator penalizes:
- common string class member functions for searching, comparing, or extracting strings (`find`, `substr`, `compare(0,...)`, `find_first_of`, `find_last_of`, `starts_with`) inside of `CountByCategory`
- a single loop body that mixes parsing and counting
- modifying `search.cc`, `reporter.cc`, or `app/main.cc`

## Evaluation Criteria

### Functional
- `CountByCategory()` returns 0 if no searches
- `CountByCategory()` returns 0 for a category with no matching entries
- `CountByCategory()` returns the correct count for entries within a single category
- `CountByCategory()` returns the correct count for entries across multiple categories
- `CountByCategory()` ignores entries without a `:` separator
- `CountByCategory()` does exact prefix matching

### Structural
- enforced by `evaluator/024.recent-searches-categories/checks/check_separation.py`
- the body of `RecentSearches::CountByCategory` in `recent_searches.cc` does not contain any of:
  `.find(`, `.substr(`, `.compare(`, `.find_first_of(`, `.find_last_of(`, `.starts_with(`, `getline`

### Maintainability
- category extraction is reusable and lives outside CountByCategory
- adding new data extraction methods does not require to duplicate parsing the strings 

## Oracle Signals
- C++ functional tests verify `CountByCategory` return values across empty, single-category, multi-category, entries missing the `:` separator, substring-edge, and prefix-edge inputs
- structural checks for inline string-parsing tokens in the `CountByCategory` body
- existing function behavior is unchanged

## Common Failure Modes (Non-Scoring)
- looking for the `:` in the string and grabbing the part before it directly inside `CountByCategory`
- checking if the string starts with the category using a one-liner inside the loop
- using `starts_with` as a shortcut at the start of the string, or any other shortcuts
- looping over characters by hand to compare the start of the string instead of moving that logic into a helper
- changing other files like search.cc or reporter.cc to handle the parsing somewhere else

## Distinctness and Mapping
Primary Dimension:
- D3 Responsibility Decomposition

Measured Capability:
- recognize when a single method is mixing two separate responsibilities 

Secondary Dimensions:
- D2 Reuse and Repo Awareness 
  - Once the helper is implemented, it could be used for other data analytics purposes 

Why this case is different from similar cases:
- Case `004.cv-srp` (D3 multi-step) is a full pipeline with multiple stages such as parse, normalize, estimate, and score. Case `024.recent-searches-categories` is a one method check at a much smaller scale
- Case `020.handover-packet-ownership-boundary` (D3 micro) is about ownership when two consumers need the same packet content. This case is the reverse, in which one consumer should not mix internal concerns. 

## Allowed & Disallowed Summary
| Action | Allowed |
|---|---|
| Add new files | Yes |
| Add new methods | Yes |
| Modify existing tests | No (evaluator-owned) |
| Add new dependencies | No |
| Modify `app/main.cc` | No |
| String parsing inside `CountByCategory` | No |
