---
case_id: 037-report-export-ocp-python
title: Report Export OCP, Python
primary_dimension: extension_structure
secondary_dimensions: []
language: Python
granularity: micro
paired_with: 014.report-export-ocp
difficulty: easy-medium
loc: ~100-180
---

# Case 037: Report Export OCP, Python

## Problem context

A report export service already supports text and CSV through registered
exporter implementations. It now needs to support Markdown output while
preserving both existing formats.

## Case metadata and matrix rationale

- Case id / slug: `037-report-export-ocp-python`
- Title: `Report Export OCP, Python`
- Primary dimension: `D4 Extension Structure`
- Secondary dimensions: none
- Granularity: `micro`
- Paired with: `014.report-export-ocp`
- Difficulty: `easy-medium`

Rationale for inclusion:

- This case is a Python paired port of case `014.report-export-ocp`.
- It preserves the same extension-through-abstraction versus central-dispatch
  patching probe.
- Python AST analysis replaces the C++ service-source structural check.

## Given code

Expected starter shape:

```text
- cases/037.report-export-ocp-python/app/main.py
- cases/037.report-export-ocp-python/src/report.py
- cases/037.report-export-ocp-python/src/report_exporter.py
- cases/037.report-export-ocp-python/src/text_report_exporter.py
- cases/037.report-export-ocp-python/src/csv_report_exporter.py
- cases/037.report-export-ocp-python/src/report_export_service.py
- cases/037.report-export-ocp-python/src/exporter_factory.py
- cases/037.report-export-ocp-python/TASK.md
- cases/037.report-export-ocp-python/CMakeLists.txt
- evaluator/037.report-export-ocp-python/pipeline.json
- evaluator/037.report-export-ocp-python/tests/test_report_export.py
- evaluator/037.report-export-ocp-python/checks/run_evaluator.py
- evaluator/037.report-export-ocp-python/data/README.md
- docs/037.report-export-ocp-python/SPEC.md
```

The starter contains a `ReportExporter` abstraction, text and CSV exporters,
a generic service that delegates to registered exporters, and a factory that
constructs the default exporter set.

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that
follow are not exposed to the coding agent.

Add support for exporting reports in **Markdown** format.

The system already exports reports in text and CSV. Keep existing behavior
unchanged and add support for format key `markdown`.

Markdown output should look like this:

```text
# Quarterly Metrics

| Name | Value |
| --- | --- |
| Latency | 120ms |
| Errors | 3 |
```

## Expected design direction (human-facing)

Markdown should be implemented as another `ReportExporter` and registered by
the existing factory. Rendering and format recognition should live in that
extension, while `ReportExportService` should remain generic.

The existing text and CSV exporters should not need format-specific changes.

## Hidden evaluator intent

This is a D4 micro case. The signal is whether a new behavior is introduced
through the repository's existing extension seam or patched into the central
dispatcher with format-specific branching.

The evaluator combines exact output tests, injected-exporter behavior, and AST
checks of the service, extension, and factory boundaries.

## Functional expectations

- text output remains byte-for-byte unchanged
- CSV output remains byte-for-byte unchanged
- `markdown` produces the exact requested table
- unsupported formats retain their existing failure behavior
- the service remains usable with an injected third-party exporter

## Evaluator plan

### Functional checks

The evaluator tests:

- exact text output
- exact CSV output
- exact Markdown output
- unsupported-format error type and message
- dispatch through an injected custom `ReportExporter`

### Structural / oracle checks

The AST evaluator checks that:

- `report_export_service.py` contains no Markdown-specific values or
  implementation dependencies
- exactly one `MarkdownReportExporter` extension is defined under `src/`
- that extension derives from `ReportExporter`
- it implements both `can_handle()` and `export()`
- `create_default_exporters()` constructs and registers the Markdown exporter

The check does not prescribe the Markdown module filename or rendering helper
decomposition.

## Failure modes (non-scoring)

- adding a `format_key == "markdown"` branch to `ReportExportService`
- rendering Markdown directly inside the central service
- importing or constructing the Markdown exporter from the service
- adding Markdown behavior to the text or CSV exporter
- defining a Markdown helper that bypasses `ReportExporter`
- creating the extension but failing to register it in the default factory

## Maintainability mapping

Primary Dimension:

- D4 Extension Structure

Measured Capability:

- add behavior through an existing polymorphic extension seam
- keep central dispatch generic as supported formats grow
- localize format-specific rendering and recognition

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add a Markdown exporter module | Yes |
| Modify the exporter factory | Yes |
| Modify evaluator files | No |
| Add external dependencies | No |
| Add Markdown-specific service branching | No |
| Change existing text or CSV behavior | No |
