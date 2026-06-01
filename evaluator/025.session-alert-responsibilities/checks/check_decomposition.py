"""Structural check for case 025: session alert responsibilities.

This case probes D3 (responsibility decomposition).  The functional task asks
the agent to add two new anomaly families (drift, leak) to a monitor that
currently only reports range alerts.  Both a cleanly decomposed solution and a
tangled one (all three families computed inside a single function) pass the
functional tests, so the structural check is the oracle for the dimension.

Rule enforced:

    No single function may produce more than one of the three alert families.

A function "produces" a family if its body either names that family's alert
type (e.g. ``RangeAlert``), appends to that family's report vector directly
(e.g. ``range_alerts.push_back(...)`` / ``.emplace_back(...)``), or appends
through a reference alias bound to that vector (e.g.
``auto& r = report.range_alerts; r.emplace_back(...)`` or
``std::vector<RangeAlert>& r = ...; r.push_back(...)``).  Whole-vector
assignment (``report.range_alerts = ...``) is deliberately NOT a signal, so a
thin orchestrator that only routes returned vectors is never flagged.

Positive arm: each family must be produced by a function REACHABLE from
``analyze()`` (directly or transitively), so an unfinished solution cannot
vacuously pass and dead one-family helpers cannot pad the check.
"""

import pathlib
import re
import sys

_FAMILIES = ("range", "drift", "leak")
_ALERT_TYPE = {"range": "RangeAlert", "drift": "DriftAlert", "leak": "LeakAlert"}

# Reference-binding to a per-family alerts vector.  Catches:
#   auto& X = report.range_alerts;
#   const auto&& X = ....range_alerts;
#   auto* X = &something.drift_alerts;
#   Foo& X = ...leak_alerts;
_ALIAS_MEMBER_RE = re.compile(
    r"(?:const\s+)?"
    r"(?:auto\s*&{1,2}|auto\s*\*+|[A-Za-z_][\w:<>,]*\s*[&*]+)"
    r"\s+(\w+)\s*=\s*[^=;]*?\.(range|drift|leak)_alerts\b"
)

# Typed-vector reference also binds an alias to its family by element type:
#   std::vector<RangeAlert>& X = some_call();
_TYPED_ALIAS_RE = re.compile(
    r"std::vector\s*<\s*(Range|Drift|Leak)Alert\s*>\s*[&*]+\s*(\w+)\s*="
)

_CONTROL_KEYWORDS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "sizeof",
    "do",
}

# A function definition opening: an identifier, a parenthesised parameter list
# that contains no ``;`` `{` `}` (so control statements and most non-function
# constructs are excluded), optional trailing qualifiers, then the body brace.
_FUNC_OPEN = re.compile(
    r"\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*"
    r"(?:const|noexcept|override|final|->|[\w:<>,&*\s])*\{"
)


def strip_comments_and_strings(text: str) -> str:
    """Blank out comments and string/char literals so tokens only match code."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    text = re.sub(r"'(?:\\.|[^'\\])+'", "''", text)
    return text


def function_bodies(text: str):
    """Yield (name, body) for every function/method body in ``text``."""
    for match in _FUNC_OPEN.finditer(text):
        name = match.group(1)
        if name in _CONTROL_KEYWORDS:
            continue
        open_brace = match.end() - 1
        depth = 0
        i = open_brace
        n = len(text)
        while i < n:
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        yield name, text[open_brace : i + 1]


def _aliases_in(body: str):
    """Return {family: set(alias names)} for reference aliases inside one body."""
    aliases = {fam: set() for fam in _FAMILIES}
    for m in _ALIAS_MEMBER_RE.finditer(body):
        aliases[m.group(2)].add(m.group(1))
    for m in _TYPED_ALIAS_RE.finditer(body):
        aliases[m.group(1).lower()].add(m.group(2))
    return aliases


def families_in(body: str) -> set:
    """Alert families produced inside one function body, alias-aware."""
    aliases = _aliases_in(body)
    push = r"(?:push_back|emplace_back)"
    produced = set()
    for fam in _FAMILIES:
        alert = _ALERT_TYPE[fam]
        member = f"{fam}_alerts"
        if re.search(rf"\b{alert}\b", body):
            produced.add(fam)
            continue
        if re.search(rf"\b{member}\s*(?:\.|->)\s*{push}\b", body):
            produced.add(fam)
            continue
        if aliases[fam]:
            alt = "|".join(re.escape(a) for a in aliases[fam])
            if re.search(rf"\b(?:{alt})\s*(?:\.|->)\s*{push}\b", body):
                produced.add(fam)
    return produced


def _callees(body: str, known: set) -> set:
    """Function names called inside ``body`` that are defined in this case."""
    out = set()
    for m in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", body):
        cand = m.group(1)
        if cand in known and cand not in _CONTROL_KEYWORDS:
            out.add(cand)
    return out


def _reachable_from(entry: str, calls_map: dict) -> set:
    """Closure of names reachable from ``entry`` through the call graph."""
    seen = set()
    stack = [entry]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        for c in calls_map.get(n, ()):
            if c not in seen:
                stack.append(c)
    return seen


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: check_decomposition.py <case_dir>")
        return 1

    case_dir = pathlib.Path(sys.argv[1]).resolve()
    src_dir = case_dir / "src"

    src_files = sorted(src_dir.rglob("*.h")) + sorted(
        list(src_dir.rglob("*.cc")) + list(src_dir.rglob("*.cpp"))
    )
    if not src_files:
        print(f"No source files found under {src_dir}")
        return 1

    funcs: dict[str, list[str]] = {}
    all_bodies: list[tuple[pathlib.Path, str, str]] = []
    for path in src_files:
        try:
            text = strip_comments_and_strings(path.read_text())
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to read {path}: {exc}")
            return 1
        rel = path.relative_to(case_dir)
        for name, body in function_bodies(text):
            funcs.setdefault(name, []).append(body)
            all_bodies.append((rel, name, body))

    known_names = set(funcs.keys())
    violations: list[str] = []

    # ---- Negative arm: no function may produce two or more families. ----
    for rel, name, body in all_bodies:
        fams = families_in(body)
        if len(fams) >= 2:
            violations.append(
                f"{rel}: function '{name}' produces multiple alert families "
                f"({', '.join(sorted(fams))}). Each anomaly family should be "
                "owned by its own unit; one function should not assemble more "
                "than one."
            )

    # ---- Positive arm: every family must be produced by a reachable fn. ----
    calls_map = {
        name: set().union(*(_callees(body, known_names) for body in bodies))
        for name, bodies in funcs.items()
    }

    if "analyze" not in known_names:
        violations.append(
            "Public entry analyze() is missing. It must remain defined and "
            "callable by the functional tests."
        )
        reachable: set = set()
    else:
        reachable = _reachable_from("analyze", calls_map)

    produced_reachable: set = set()
    for name in reachable:
        for body in funcs[name]:
            produced_reachable |= families_in(body)

    missing = set(_FAMILIES) - produced_reachable
    if missing:
        violations.append(
            "No reachable producer found for alert families: "
            f"{', '.join(sorted(missing))}. Each anomaly family must be "
            "produced by code that analyze() actually invokes (directly or "
            "transitively); unused helpers do not count."
        )

    if violations:
        for v in violations:
            print(v)
        return 1

    print("Decomposition check passed: each alert family is owned separately.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
