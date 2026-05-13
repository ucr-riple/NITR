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
