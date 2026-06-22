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
