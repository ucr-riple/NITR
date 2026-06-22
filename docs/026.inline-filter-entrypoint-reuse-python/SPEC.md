---
case_id: 026-inline-filter-entrypoint-reuse-python
title: Inline Filter Parsing, Python
primary_dimension: reuse
secondary_dimensions:
  - change_locality
language: Python
granularity: micro
paired_with: 021.inline-filter-entrypoint-reuse
difficulty: easy-medium
loc: 150-250
---

# Case 026: Inline Filter Parsing, Python

## Problem context

The repository implements issue filtering for a small CLI tool. It already supports parsing filter rules from a structured clause object used by config-style inputs and tests. Product now wants a single inline clause string for command-line usage. The feature should stay small: one clause, a narrow syntax, and no broader query language.

## Case metadata and matrix rationale

- Case id / slug: `026-inline-filter-entrypoint-reuse-python`
- Title: `Inline Filter Parsing, Python`
- Primary dimension: `D2 Reuse and Repo Awareness`
- Secondary dimensions: minor `D1 Change Locality`
- Granularity: `micro`
- Paired with: `021.inline-filter-entrypoint-reuse`
- Difficulty: `easy-medium`

Rationale for inclusion:

- This case is a Python paired port of case `021-inline-filter-entrypoint-reuse`.
- It preserves the same maintainability probe while validating whether the evaluator and case conventions remain robust across languages.
- The central question is unchanged: when a new input boundary is added, does the implementation reuse the repository's existing interpretation path or introduce a shadow parser and validation path?

## Given code

The starter repository should run successfully and all provided tests should pass. The initial code should remain small and centered on one parsing subsystem.

Expected starter shape:

```text
- cases/026.inline-filter-entrypoint-reuse-python/app/main.py
- cases/026.inline-filter-entrypoint-reuse-python/src/filter_clause.py
- cases/026.inline-filter-entrypoint-reuse-python/src/filter_rule.py
- cases/026.inline-filter-entrypoint-reuse-python/src/filter_parser.py
- cases/026.inline-filter-entrypoint-reuse-python/src/filter_validation.py
- cases/026.inline-filter-entrypoint-reuse-python/TASK.md
- cases/026.inline-filter-entrypoint-reuse-python/CMakeLists.txt
- evaluator/026.inline-filter-entrypoint-reuse-python/pipeline.json
- evaluator/026.inline-filter-entrypoint-reuse-python/data
- evaluator/026.inline-filter-entrypoint-reuse-python/tests
- docs/026.inline-filter-entrypoint-reuse-python/SPEC.md
```

Starter design assumptions:

- `FilterClause` is the existing structured input form. It stores three strings such as `field`, `op`, and `value`.
- `FilterRule` is the canonical internal representation. It should use parsed enums or stable symbolic values and typed values rather than raw input strings.
- The existing parser path already accepts a `FilterClause` and returns either a parsed `FilterRule` or a normalized parse error.
- Validation already exists for supported fields, supported operators, allowed field/operator combinations, and typed value parsing such as integer parsing for `priority`.
- Existing tests already cover the structured-clause path for both valid and invalid cases.

The starter code should make the existing parse-and-validation flow discoverable through normal repository reading, but it should not reduce the task to a one-symbol grep exercise.

## Agent-facing contract

The following section is the full text of `TASK.md`. The internal sections that follow are not exposed to the coding agent.

# Inline Filter Parsing

## Background

This repository already parses issue filter rules from a structured clause object with separate `field`, `op`, and `value` strings. That path is used by the current config-style input and existing tests.

We now need a small inline form for command-line usage. The new input is a single string that represents one filter clause and should produce the same rule result and invalid-input behavior as the existing structured-clause path.

## Required change

Add support for parsing one inline issue filter clause string.

Supported fields:
- `status`
- `priority`
- `owner`

Supported operators:
- `=`
- `>=`
- `:`

Supported examples:
- `status=open`
- `status = open`
- `priority>=3`
- `owner : alice`

This change is only for a single clause. Do not add support for multiple clauses, `AND` / `OR`, parentheses, new fields, or new operators.

## Behavior requirements

- Valid inline input must produce the same parsed rule as the equivalent structured clause input.
- Leading and trailing whitespace around the full expression should be ignored.
- Whitespace around the operator should be accepted.
- Invalid field names should fail using the existing invalid-input behavior.
- Invalid operators should fail using the existing invalid-input behavior.
- Invalid values should fail using the existing invalid-input behavior.
- Keep the current structured-clause behavior unchanged.

## Implementation constraints

- Keep the change focused on this parsing feature.
- Do not modify files under `evaluator/026.inline-filter-entrypoint-reuse-python/`.
- Do not add new dependencies.
- Keep existing public behavior unchanged except for the new inline parsing support.

## Build and test

The project must continue to run successfully, and all existing tests must still pass after the change.

## Internal design direction

Acceptable solutions may vary in exact decomposition, but they should keep the new feature small and localized. The preferred high-level shape is a thin inline parsing entrypoint that adapts the input string into the existing internal parsing flow before most field, operator, and value interpretation has happened.

`parse_inline_filter` may identify the inline field/operator/value boundaries, but semantic interpretation must remain downstream. It should not decide whether a field is supported, whether an operator is valid, how a typed value is parsed, or which normalized error category should be returned.

Good solution characteristics:

- one downstream authority remains responsible for converting filter input into `FilterRule`
- validation behavior remains consistent across structured and inline inputs
- error categorization remains consistent across structured and inline inputs
- the new feature adds minimal new public surface

The specification should not require one exact class or function name. It should require convergence in behavior and ownership.

## Hidden evaluator intent

This is a D2 micro case. The maintainability signal is whether the implementation discovers and reuses the repository's existing parsing and validation affordances when adding a new input boundary.

The task is intentionally small:

- one new input form
- one clause at a time
- no boolean composition
- no new IO
- no architectural redesign request

The case is not primarily about syntax design or decomposition cleanup. The central question is whether the repository continues to have one effective interpretation path for filter clauses, or whether the implementation introduces a second shadow path for field/operator/value meaning.

## Functional expectations

Supported inline syntax:

- fields: `status`, `priority`, `owner`
- operators: `=`, `>=`, `:`
- exactly one clause per string
- surrounding whitespace is ignored
- whitespace around the operator is allowed

Valid examples:

- `status=open`
- `status = open`
- `priority>=3`
- `priority >= 3`
- `owner:alice`
- `owner : alice`

Invalid examples:

- `tag=open` because `tag` is not a supported field
- `priority>3` because `>` is not a supported operator
- `priority>=high` because `priority` expects an integer value
- `status` because the clause is incomplete
- `status=open=closed` because the clause is malformed

Expected behavior:

- valid inline input returns the same canonical `FilterRule` as the equivalent structured-clause input
- invalid inline input returns the same stable error category, error code, or equivalent normalized failure payload as the equivalent structured-path failure
- all existing structured-clause behavior remains unchanged

## Evaluator plan

### Functional checks

The evaluator should add or run tests for:

- successful parsing of each supported field/operator form
- accepted whitespace variations
- invalid field
- invalid operator
- invalid typed value
- malformed clause input
- any starter-defined operator/field mismatch case, if the starter repo has one

All existing tests must continue to pass.

### Behavior-parity / path-convergence checks

This is the primary oracle.

For each test fixture:

- create the corresponding structured `FilterClause`
- parse it through the existing structured path
- parse the equivalent inline string through the new path
- compare success vs failure
- compare canonical `FilterRule` results for successful parses
- compare stable error category or code for unsuccessful parses

The key signal is that both input forms converge on the same interpretation and validation behavior.

### Structural / oracle checks

Structural checks should be limited and should avoid dependence on one exact helper name or one exact internal decomposition.

Recommended checks:

- the new inline entrypoint should live in or route into the existing parser subsystem, not a separate unrelated parser module
- newly added code should not contain substantial duplicate field/operator/value interpretation outside the existing parser and validation area
- newly added code should not add a second validation path for supported fields and operators
- direct construction of canonical `FilterRule` inside the inline entrypoint should be treated as suspicious if the structured path already owns that work

These checks are secondary. They are meant to catch obvious shadow-parser implementations, not to force one exact refactoring shape.

### Distinguishing convergence from shadow reimplementation

Good solutions are favored because:

- structured and inline inputs behave the same on both valid and invalid cases
- the new code mainly adapts the input form and defers interpretation and validation to the existing downstream flow

Bad solutions are disfavored because:

- they interpret field/operator/value meaning in a mostly separate inline-only path
- they duplicate validation rules or error construction locally
- they may call one existing helper but still keep most interpretation logic duplicated

The evaluator should not accept a symbolic call to one shared helper as sufficient evidence of a good design.

## Anti-patterns / failure modes

- Parallel parser:
  - The inline feature manually splits and interprets the string into `FilterRule` without flowing through the existing parser path.
- Duplicated validation:
  - Supported fields, operators, or typed-value checks are reimplemented locally for inline parsing.
- Bypassing the canonical internal representation:
  - The inline path constructs final rule objects directly instead of passing through the same downstream representation and error handling used by structured input.
- Superficial reuse:
  - The implementation calls one existing helper, such as an error formatter, but still keeps most field/operator/value interpretation in new inline-only code.
- Unnecessary API growth:
  - The change introduces broad new parser surfaces or helper modules for a feature that should remain one small entrypoint.

## Maintainability mapping

Primary Dimension:
- D2 Reuse and Repo Awareness

Measured Capability:
- recognize and reuse an existing parse/validate path when adding a new input boundary
- preserve one effective authority for filter interpretation and invalid-input handling

Secondary Dimensions:
- D1 Change Locality

## Allowed & Disallowed Summary

| Action | Allowed |
|---|---|
| Add new files | Yes |
| Modify existing parser logic | Yes |
| Modify evaluator files | No |
| Add new dependencies | No |
| Introduce a separate inline-only parser subsystem | No |
| Keep structured-clause behavior unchanged | Yes |
