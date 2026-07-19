# Task

Implement support for a compact rendering mode in the inventory report.

## Requirements

Add a new field to `ReportOptions`:

- `compact_mode` with default value `False`

Keep the existing full mode behavior unchanged.

When `compact_mode` is `True`:

- the header must be exactly:
  `Inventory Report (compact)`
- each row must be rendered as:
  `<id>:<name>:<quantity>`
- if `include_summary` is `True`, the summary must be exactly:
  `Total quantity: <sum>`
- if `include_summary` is `False`, omit the summary
