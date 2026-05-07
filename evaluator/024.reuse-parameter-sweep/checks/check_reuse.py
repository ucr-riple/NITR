#!/usr/bin/env python3
"""
check_reuse.py — Structural reuse checks for case 024.

Enforces two rules:
  1. sweep_warmup_x_lr must call run_trial, pick_best, and compute_summary,
     and must not contain runner-internal fingerprints (reimplementation signal).
  2. app/main.cc must match the frozen golden baseline.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ── Runner-internal fingerprints ──────────────────────────────────────────────
# These patterns appear in runner.cc's xorshift and loss formula.
# Their presence inside sweep_warmup_x_lr's body signals inline reimplementation.
RUNNER_FINGERPRINTS = [
    re.compile(r'0xDEADBEEF', re.IGNORECASE),
    re.compile(r'\bstd::log1p\b'),
    re.compile(r'<<\s*13'),   # xorshift step unique to runner.cc
]

# ── Golden app/main.cc ────────────────────────────────────────────────────────
GOLDEN_MAIN = """\
#include <iostream>
#include <string>
#include <vector>
#include "runner.h"
#include "sweeps.h"

int main(int argc, char** argv) {
  using namespace nitr::case024;

  TrialParams base{};
  base.seed = 42;
  base.learning_rate = 0.01;
  base.batch_size = 32;
  base.warmup_steps = 0;

  const std::vector<double> lr_grid     = {0.001, 0.01, 0.1};
  const std::vector<int>    batch_sizes  = {16, 32, 64};
  const std::vector<int>    warmup_steps = {0, 50, 100, 200};

  if (argc < 2) {
    std::cerr << "Usage: " << argv[0]
              << " <lr|batch_x_lr|warmup_x_lr>\\n";
    return 1;
  }

  const std::string cmd = argv[1];
  if (cmd == "lr") {
    auto r = sweep_learning_rate(base, lr_grid);
    std::cout << "best_idx=" << r.best_idx
              << " loss=" << r.results[r.best_idx].loss << "\\n";
  } else if (cmd == "batch_x_lr") {
    auto r = sweep_batch_size_x_lr(base, batch_sizes, lr_grid);
    std::cout << "best_idx=" << r.best_idx
              << " loss=" << r.results[r.best_idx].loss << "\\n";
  } else if (cmd == "warmup_x_lr") {
    auto r = sweep_warmup_x_lr(base, warmup_steps, lr_grid);
    std::cout << "best_idx=" << r.best_idx
              << " loss=" << r.results[r.best_idx].loss << "\\n";
  } else {
    std::cerr << "Unknown command: " << cmd << "\\n";
    return 1;
  }
  return 0;
}
"""


# ── Utilities ─────────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    """Normalize line endings and strip trailing whitespace per line."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    while lines and not lines[-1]:
        lines.pop()
    return '\n'.join(lines) + '\n'


def strip_line_comments(source: str) -> str:
    """Remove // … line comments to avoid false positives on commented-out code."""
    return re.sub(r'//[^\n]*', '', source)


def extract_function_body(source: str, func_name: str) -> str:
    """
    Return the body (including outer braces) of the first *definition* of
    func_name found in source.  A definition has '{' after the parameter list;
    a declaration has ';'.  Returns '' if not found.
    """
    pattern = re.compile(r'\b' + re.escape(func_name) + r'\s*\(')
    for m in pattern.finditer(source):
        # Walk from the opening '(' to find the matching ')'.
        i = m.end() - 1  # position of '('
        depth = 0
        while i < len(source):
            if source[i] == '(':
                depth += 1
            elif source[i] == ')':
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
        # Skip to the next '{' or ';'.
        while i < len(source) and source[i] not in ('{', ';'):
            i += 1
        if i >= len(source) or source[i] == ';':
            continue  # declaration, not definition
        # Brace-count to extract the full body.
        start = i
        brace_depth = 0
        for j in range(i, len(source)):
            if source[j] == '{':
                brace_depth += 1
            elif source[j] == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    return source[start:j + 1]
    return ''


def fail(error: str, details: dict) -> None:
    print(json.dumps({'ok': False, 'error': error, 'details': details}, indent=2))
    sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description='Structural reuse check for case 024.')
    ap.add_argument('case_root', help='Path to the case root directory.')
    args = ap.parse_args()

    root = Path(args.case_root)
    sweeps_path = root / 'src' / 'sweeps.cc'
    main_path   = root / 'app' / 'main.cc'

    sweeps_src = sweeps_path.read_text(encoding='utf-8') if sweeps_path.exists() else ''
    main_src   = main_path.read_text(encoding='utf-8')   if main_path.exists()   else ''

    if not sweeps_src:
        fail('ERR_SWEEPS_UNREADABLE', {'path': str(sweeps_path)})

    # ── Rule 2: frozen file ───────────────────────────────────────────────────
    if normalize(main_src) != normalize(GOLDEN_MAIN):
        fail('ERR_MAIN_MODIFIED', {
            'path': str(main_path),
            'note': 'app/main.cc must match the frozen golden baseline.',
        })

    # ── Rule 1: sweep_warmup_x_lr delegation checks ───────────────────────────
    body_warmup = extract_function_body(sweeps_src, 'sweep_warmup_x_lr')
    if not body_warmup:
        fail('ERR_SWEEP_WARMUP_NOT_FOUND', {
            'note': 'Could not locate a definition of sweep_warmup_x_lr in src/sweeps.cc.',
        })

    body_warmup_clean = strip_line_comments(body_warmup)

    for token, name in [
        ('run_trial(',       'run_trial'),
        ('pick_best(',       'pick_best'),
        ('compute_summary(', 'compute_summary'),
    ]:
        if token not in body_warmup_clean:
            fail(f'ERR_SWEEP_WARMUP_MISSING_{name.upper()}', {
                'missing': token,
                'note': f'sweep_warmup_x_lr must call {token}.',
            })

    for fp in RUNNER_FINGERPRINTS:
        if fp.search(body_warmup_clean):
            fail('ERR_SWEEP_WARMUP_RUNNER_REIMPLEMENTED', {
                'pattern': fp.pattern,
                'note': (
                    'sweep_warmup_x_lr appears to contain runner internals. '
                    'Call run_trial() instead of reimplementing trial execution.'
                ),
            })

    # ── All checks passed ─────────────────────────────────────────────────────
    print(json.dumps({
        'ok': True,
        'checks': {
            'main_frozen':                        True,
            'sweep_warmup_calls_run_trial':       True,
            'sweep_warmup_calls_pick_best':       True,
            'sweep_warmup_calls_compute_summary': True,
            'sweep_warmup_no_runner_internals':   True,
        },
    }, indent=2))
    sys.exit(0)


if __name__ == '__main__':
    main()
