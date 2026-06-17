# 011. config-sprawl

## Summary

This case evaluates whether an agent can add a new configuration-driven behavior without causing parameter sprawl or unnecessary change amplification.

The system renders a small inventory report from a list of items. A public `ReportOptions` configuration object already exists. The new requirement adds a `compact_mode` option that changes multiple parts of rendering behavior.

The maintainability question is not whether the agent can make the output correct. It is whether the agent keeps the change localized by extending the existing configuration boundary, instead of threading new standalone parameters through helper functions across the renderer.

## Maintainability Dimension

- **Primary dimension:** configuration growth
- **Secondary dimensions:** change locality, API hygiene

## Why this case exists

AI coding agents often satisfy a new option by pushing an extra `bool` or `enum` through multiple layers of helper functions. The code still works, but the design accumulates maintenance debt:

- more signatures change than necessary;
- the same option is manually forwarded through multiple call chains;
- future options compound the problem.

This case isolates that behavior in a small, automatable C++ setting.

## Repository Shape

The case follows this layout:

- `cases/011.config-sprawl/app/main.cc`
- `cases/011.config-sprawl/src/`
- `cases/011.config-sprawl/TASK.md`
- `cases/011.config-sprawl/CMakeLists.txt`
- `evaluator/011.config-sprawl/pipeline.json`
- `evaluator/011.config-sprawl/tests/`
- `evaluator/011.config-sprawl/data/`
- `docs/011.config-sprawl/SPEC.md`

## Existing behavior

The starter repository already contains:

- item and report data types;
- `ReportOptions`, currently with `include_summary`;
- a renderer entry point:
  - `std::string RenderInventoryReport(const std::vector<Item>& items, const ReportOptions& options);`
- internal helpers that render header, rows, and footer.

The current implementation ignores `compact_mode` because it does not exist yet.

## Required change

Add support for a new option:

- `ReportOptions::compact_mode` (default `false`)

When `compact_mode == false`, the existing full rendering style should remain unchanged.

When `compact_mode == true`, rendering must change as follows:

### Compact header

Use:

```text
Inventory Report (compact)
```

instead of the full header:

```text
Inventory Report
Items: <count>
```

### Compact rows

Each row should use:

```text
<id>:<name>:<quantity>
```

Example:

```text
A-1:apple:5
```

instead of:

```text
- id=A-1, name=apple, qty=5
```

### Compact summary

If `include_summary == true`, use:

```text
Total quantity: <sum>
```

for compact mode.

If `include_summary == false`, omit the summary entirely in both modes.

## Good solution characteristics

A good solution typically does one of the following:

- extends `ReportOptions` and uses it as the configuration boundary;
- keeps the public API stable except for the intended extension to `ReportOptions`;
- avoids adding raw `compact_mode` parameters to multiple helper functions;
- keeps configuration logic localized inside the renderer implementation.

## Bad solution characteristics

A bad solution typically:

- adds `bool compact_mode` to several helper signatures;
- forwards `compact_mode` manually through multiple layers;
- expands the change surface far beyond what the new option requires;
- couples unrelated helpers to configuration plumbing.

## Oracle Signals

### Functional oracle

The evaluator checks:

- full mode output remains unchanged;
- compact mode output matches exactly;
- summary omission still works;
- compact mode and summary interact correctly.

### Structural / maintainability oracle

The evaluator checks for signature-level parameter sprawl:

- helper declarations/definitions in `src/report_renderer.h` and `src/report_renderer.cc` must not introduce standalone `compact_mode` parameters;
- the change should be expressed through the existing `ReportOptions` boundary or an equivalently localized internal design.

## Expected failure mode

A typical weak agent will patch the code by threading `compact_mode` through helper functions such as header/row/footer renderers. Functional tests may pass, but the structural oracle should fail.

## TASK.md

`TASK.md` is the agent-facing subset of this specification. It should contain only the implementation task and concrete output requirements. It must stay brief and must not reveal the evaluation purpose of the case.
