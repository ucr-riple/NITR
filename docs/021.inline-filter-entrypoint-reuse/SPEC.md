---
case_id: 021-inline-filter-parser-reuse
title: Inline Filter Parsing
primary_dimension: reuse
secondary_dimensions:
  - change_locality
language: C++
difficulty: easy-medium
loc: 150-250
---

# Case 021: Inline Filter Parsing

## Problem context

The repository implements issue filtering for a small CLI tool. It already supports parsing filter rules from a structured clause object used by config-style inputs and tests. Product now wants a single inline clause string for command-line usage. The feature should stay small: one clause, a narrow syntax, and no broader query language.

## Case metadata and matrix rationale

- Case id / slug: `021-inline-filter-parser-reuse`
- Title: `Inline Filter Parsing`
- Primary dimension: `D2 Reuse and Repo Awareness`
- Secondary dimensions: minor `D1 Change Locality`
- Difficulty: `easy-medium`
- Rationale for inclusion:
  - The design matrix has an open D2 micro slot.
  - This case adds a small, realistic probe where a new input boundary should feed into behavior the repository already supports.
  - It complements the existing D2 cases by focusing on a thin adapter-style feature instead of a broader feature or implementation-step reuse task.

## Given code

The starter repository should compile and all provided tests should pass. The initial code should remain small and centered on one parsing subsystem.

Expected starter shape:

```text
- cases/021.inline-filter-entrypoint-reuse/app/main.cc
- cases/021.inline-filter-entrypoint-reuse/src/filter_rule.h
- cases/021.inline-filter-entrypoint-reuse/src/filter_clause.h
- cases/021.inline-filter-entrypoint-reuse/src/filter_parser.h
- cases/021.inline-filter-entrypoint-reuse/src/filter_parser.cc
- cases/021.inline-filter-entrypoint-reuse/src/filter_validation.h
- cases/021.inline-filter-entrypoint-reuse/src/filter_validation.cc
- cases/021.inline-filter-entrypoint-reuse/TASK.md
- cases/021.inline-filter-entrypoint-reuse/CMakeLists.txt
- evaluator/021.inline-filter-entrypoint-reuse/pipeline.json
- evaluator/021.inline-filter-entrypoint-reuse/data
- evaluator/021.inline-filter-entrypoint-reuse/tests
- docs/021.inline-filter-entrypoint-reuse/SPEC.md
```

Starter design assumptions:

- `FilterClause` is the existing structured input form. It stores three strings such as `field`, `op`, and `value`.
- `FilterRule` is the canonical internal representation. It should use parsed enums and typed values rather than raw input strings.
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
- Do not modify files under `evaluator/021.inline-filter-entrypoint-reuse/`.
- Do not add new dependencies.
- Keep existing public behavior unchanged except for the new inline parsing support.

## Build and test

The project must continue to compile, and all existing tests must still pass after the change.

## Internal design direction

Acceptable solutions may vary in exact decomposition, but they should keep the new feature small and localized. The preferred high-level shape is a thin inline parsing entrypoint that adapts the input string into the existing internal parsing flow before most field, operator, and value interpretation has happened.

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
- the specification should prefer stable error categories or codes over brittle exact string matching
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
- compare stable error category / code / normalized failure payload for unsuccessful parses

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

## Separation analysis

### Difference from case 003

Case `003` is closer to a feature or implementation-step reuse probe: an existing implementation block already performs the needed work, and the question is whether the agent reuses that block rather than rewriting it.

Case `021` is different in starter shape and failure mode:

- the starter repository already supports one input boundary, `FilterClause`
- that boundary flows into a multi-stage parser and validation path
- the new feature adds a second boundary, an inline clause string
- the important distinction is whether both boundaries converge into the same downstream interpretation path

The failure here is not simply "did not call function X." The broader failure is that the repository ends up with two places that decide what fields, operators, typed values, and invalid combinations mean.

### Distinct case-suite value

This case adds D2 micro coverage for adapter-style repository reuse. It targets a common maintenance scenario where a new convenience input surface should preserve one existing interpretation path, rather than copy it.

That makes it meaningfully different from a generic "use the existing helper" task and fills a gap in the current matrix.

## Maintainability mapping

Primary Dimension:
- Reuse and Repo Awareness

Measured Capability:
- Detect an existing parsing and validation affordance in a small repository
- Add a new input boundary without forking interpretation behavior

Secondary Dimensions:
- Change Locality

## Allowed & disallowed summary

| Action | Allowed |
|--------------------------------|---------|
| Add new files | Yes, if necessary |
| Modify existing core logic | Yes |
| Modify existing tests | No |
| Add new dependencies | No |
| Modify public headers | Yes, if needed |
| Use global mutable state | No |
| Introduce new external IO | No |

## Packaging notes

This case fits the standard package layout directly:

- `cases/021.inline-filter-entrypoint-reuse/src/` contains a compact parsing and validation subsystem
- `cases/021.inline-filter-entrypoint-reuse/app/main.cc` can expose the inline parser in a minimal demonstration path
- `evaluator/021.inline-filter-entrypoint-reuse/tests/` can compare structured and inline parsing outcomes using matched fixtures
- `evaluator/021.inline-filter-entrypoint-reuse/pipeline.json` can express limited structural checks for obvious shadow parsers
- `evaluator/021.inline-filter-entrypoint-reuse/data/` can hold matched valid and invalid examples if the harness prefers data-driven tests

Notes for starter-code and evaluator generation:

- keep the core starter code small, roughly 150-250 LOC before evaluator files
- include a stable parse error representation if possible, such as an error code enum or normalized category
- ensure the existing structured-clause path is readable and discoverable without making the intended downstream flow mechanically obvious from one symbol name alone
- keep the syntax narrow and fixed so the case remains micro
