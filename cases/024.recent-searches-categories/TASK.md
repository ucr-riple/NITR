### Task

Data analytics team needs a per-category count of recent searches. Complete the existing `RecentSearches` class by implementing a method named `CountByCategory` that accepts a category and returns how many entries in recent-searches belong to that category.

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