# Submit Backend Architecture Refactor Plan

## Status

Follow-up work after the `opencode-cli` backend integration. This refactor must
be delivered separately from issue #95 so the OpenCode feature remains easy to
review and validate.

Implementation progress: all provider implementations have been extracted and
the legacy `submit/backends.py` module has been removed. The flat transitional
modules remain in place; moving them into the final `submit/backends/` package
is the next behavior-preserving phase.

## Motivation

Before extraction, `submit/backends.py` owned several unrelated responsibilities:

- backend defaults and registration
- API and CLI invocation
- authentication/configuration handling
- prompts and provider payloads
- retry policies
- response and usage decoding
- response artifact persistence
- per-backend task orchestration

As more providers are added, this structure increases merge conflicts, makes
backend-specific behavior harder to test, and encourages unrelated backends to
share policy accidentally.

The goal is to split providers into focused modules behind a small common
interface without changing submission behavior, output layout, evaluator
behavior, or benchmark semantics.

## Non-goals

This refactor will not:

- change backend command lines, prompts, defaults, or authentication
- unify provider retry policies that are intentionally different
- change the JSON replacement contract
- change staging, multi-step, Pass@N, or Stability behavior
- introduce dynamic plugin discovery or third-party backend loading
- force API and CLI backends through one large inheritance hierarchy
- redesign `submit_case.py`, the evaluator, or Docker execution
- add or remove a backend

## Design Principles

### Thin interface

Use a small interface for registration and dispatch. Avoid a base class that
contains provider conditionals or assumes every backend has the same lifecycle.

Recommended interface:

```python
from typing import Mapping, Protocol


class SubmissionBackend(Protocol):
    name: str
    defaults: Mapping[str, object]

    def run(self, args) -> None:
        ...
```

A frozen descriptor is also acceptable:

```python
@dataclass(frozen=True)
class BackendDefinition:
    name: str
    defaults: Mapping[str, object]
    runner: Callable[[argparse.Namespace], None]
```

Prefer the descriptor if backend implementations remain function-oriented.
Do not introduce classes solely to wrap one existing function.

### Composition over deep inheritance

Share stable mechanisms as helpers:

- JSON replacement application
- response/transcript artifact paths
- common API request utilities
- common subprocess diagnostics
- task/staging orchestration

Keep policy owned by each backend:

- retry classification
- model/default configuration
- permission and sandbox behavior
- provider payload/response shapes
- usage extraction
- authentication requirements

OpenCode workspace isolation, for example, must remain OpenCode-specific unless
another backend adopts exactly the same benchmark contract.

### Behavior-preserving migration

Every migration step must be mechanical and independently testable. A provider
module should initially contain the existing code with minimal edits. Cleanup
and deduplication happen only after all backends are split and parity tests are
in place.

## Target Layout

The package layout below is the final state. During Phase 1, use the flat
transitional modules `submit/backend_interface.py` and
`submit/backend_registry.py` while the legacy `submit/backends.py` module still
exists. Python cannot safely host that module and a `submit/backends/` package
under the same import name. Move the transitional modules into the package only
after the compatibility module has been removed or renamed in Phase 5.

```text
submit/
├── backends/
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   ├── artifacts.py
│   ├── chatgpt_api.py
│   ├── codex_cli.py
│   ├── claude_cli.py
│   ├── claude_vertex.py
│   ├── gemini_cli.py
│   ├── gemini_vertex.py
│   ├── opencode_cli.py
│   ├── qwen_openapi.py
│   └── qwen_vertex.py
├── submit_common.py
├── submit_case.py
└── tests/
    └── backends/
```

`artifacts.py` is optional. Create it only if at least two migrated backends use
the same helpers without policy differences.

The existing `submit/backends.py` should become a temporary compatibility
facade and then be removed after all imports are migrated.

## Registry Contract

`registry.py` owns the canonical backend collection and validates it at import
or test time:

```python
BACKENDS: tuple[BackendDefinition, ...] = (...)
BACKEND_RUNNERS = {backend.name: backend.runner for backend in BACKENDS}
BACKEND_DEFAULTS = {backend.name: backend.defaults for backend in BACKENDS}
```

Validation must reject:

- duplicate names
- empty names
- missing/non-callable runners
- mutable shared default dictionaries where one run can affect another

`submit_case.py` continues deriving argparse choices from the registry. It must
not gain a second hard-coded backend list.

## Migration Phases

### Phase 0: Characterization tests

Before moving code, add credential-free tests that capture the current public
contract:

- registered backend names
- default configuration values
- parser backend choices
- `--model_name` forwarding
- representative command/payload construction for every backend
- response and usage artifact suffixes
- missing credential/binary errors
- retry counts for representative transient and semantic failures

Mock external SDKs, HTTP, and subprocesses. Do not contact providers.

Exit condition: the tests pass against the current monolithic module.

### Phase 1: Introduce interface and registry

Add:

```text
submit/backend_interface.py
submit/backend_registry.py
```

Initially register the existing functions from the compatibility module. Do not
move provider implementations yet. Use one generic function adapter for all
function-based implementations; do not add provider-specific wrapper classes.

Update `submit_case.py` to import the registry from the package while preserving
the existing `BACKEND_RUNNERS` shape.

Exit condition: no backend behavior or CLI help output changes.

### Phase 2: Move OpenCode

Move the already isolated OpenCode adapter to:

```text
submit/backends/opencode_cli.py
```

Keep its NDJSON, workspace-integrity, isolation, and retry tests unchanged.
Introduce a provider-specific class only if moving the implementation creates
real behavior or state for that class to own; otherwise continue using the
generic function adapter.

This proves the package/registry structure with a backend that has few
dependencies on the monolith.

Exit condition: OpenCode tests and registry parity tests pass.

### Phase 3: Move local CLI backends

Move in this order:

1. Gemini CLI
2. Claude CLI
3. Codex CLI

Each move should be one reviewable commit when practical. Preserve command
construction, prompts, retries, transcripts, and usage handling exactly.

After all three move, identify truly identical subprocess/artifact helpers.
Extract only helpers with matching failure and retry semantics.

Exit condition: CLI characterization tests pass without golden-output changes.

### Phase 4: Move API and Vertex backends

Move:

1. ChatGPT API
2. Claude Vertex
3. Gemini Vertex
4. Qwen OpenAPI
5. Qwen Vertex

Keep provider SDK imports inside runner functions where they are currently lazy,
so users do not need every optional dependency to run one backend or display
CLI help.

Exit condition: importing the registry requires no optional provider SDK, and
all API characterization tests pass.

### Phase 5: Remove compatibility facade

Once every backend lives in the package:

- delete provider code from `submit/backends.py`
- update all imports to `submit.backends`
- remove the facade or leave a minimal deprecated re-export only if an external
  consumer is known
- run an import search to ensure no stale references remain

Exit condition: one canonical registry and no duplicated defaults/runners.

### Phase 6: Conservative deduplication

Review repeated code only after migration. Candidate helpers include:

- transcript/usage path construction
- response artifact persistence
- bounded request-attempt logging
- common JSON-replacement task flow

Do not merge helpers when backends differ in:

- retryable failure classification
- whether invalid model output is retried
- staging/sandbox guarantees
- empty-file support
- transcript format
- usage metadata

Exit condition: helpers encode mechanisms, not provider-specific policy.

## Testing Strategy

### Registry tests

- backend names match the pre-refactor set
- names are unique
- defaults match pre-refactor values
- every runner is callable
- parser choices match registry names
- mutating a per-run config copy cannot mutate registered defaults

### Backend contract tests

For each backend, cover the behavior applicable to it:

- command or API payload construction
- explicit model override
- configured default model
- environment/credential requirements
- successful response decoding
- invalid semantic response
- transient transport failure
- terminal failure
- transcript/usage artifacts

### Integration tests

- one fake CLI backend through `submit_case.py`
- one fake API backend through `submit_case.py`
- multi-step state propagation
- `--submit-count 2` output isolation
- importing the registry without optional SDK packages installed

### Validation commands

At minimum:

```bash
python3 -m unittest discover -s submit/tests
tools/check_python_format.sh
tools/check_format.sh
python3 submit/submit_case.py --help
git diff --check
```

Run existing CTest registrations that cover submit tests as well.

## Compatibility Requirements

The refactor must preserve:

- all backend names
- all CLI flags and aliases
- all default models and timeout/retry values
- output directory and response artifact layout
- error behavior visible to `submit_case.py`
- lazy optional-dependency imports
- Docker argument forwarding
- multi-step behavior
- Pass@N/Stability semantics

Any intentional behavior change requires a separate issue/PR and must not be
hidden inside the migration.

## Risks and Mitigations

### Circular imports

Provider modules should depend on `submit_common` and small helper modules, not
on `registry.py`. The registry imports providers; providers never import the
registry.

### Shared mutable defaults

Store defaults as immutable mappings or copy them before every run. Add a test
that one backend invocation cannot change later invocations.

### Eager optional SDK imports

Keep imports such as Google/Vertex SDKs inside backend runners. Test registry
import in a minimal Python environment.

### Over-generalized retry logic

Do not create a universal retry decorator until parity tests demonstrate that
the policies are identical. Hidden additional model samples would affect
Pass@N fairness.

### Oversized migration PR

Prefer several behavior-preserving PRs or commits following the phases above.
Do not mix formatting-only rewrites with provider moves.

## Acceptance Criteria

- [ ] All backend names and defaults match the pre-refactor implementation.
- [ ] `submit_case.py` derives choices from one registry.
- [ ] Each backend implementation has its own focused module.
- [ ] Importing the registry does not require optional provider SDKs.
- [ ] No provider imports or depends on the registry.
- [ ] Existing output layouts and artifacts are unchanged.
- [ ] Multi-step and `--submit-count` behavior are unchanged.
- [ ] Retry semantics remain backend-specific and parity-tested.
- [ ] OpenCode isolation/integrity guarantees remain intact.
- [ ] The monolithic implementation/facade is removed or contains re-exports only.
- [ ] Credential-free characterization and integration tests pass.
- [ ] Documentation reflects the new internal layout where relevant.

## Recommended Delivery

Implement this plan as a dedicated follow-up issue with staged PRs or commits:

1. characterization tests plus interface/registry
2. OpenCode and local CLI migration
3. API/Vertex migration and facade removal
4. conservative helper extraction

Do not begin the refactor until issue #95 is merged or its implementation branch
is stable, to avoid mixing feature review with architecture review.
