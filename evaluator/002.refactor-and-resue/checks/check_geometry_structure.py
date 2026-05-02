#!/usr/bin/env python3

import pathlib
import re
import sys


ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.cwd()
SRC = ROOT / "src" / "geometry.cc"


def strip_comments_and_strings(text: str) -> str:
    """Remove comments and literals so regex checks focus on structural code tokens."""
    text = re.sub(r'"([^"\\]|\\.)*"', '""', text)
    text = re.sub(r"'([^'\\]|\\.)*'", "''", text)
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return text


def extract_function_body(text: str, function_name: str) -> str:
    """Return the body text for a named function using brace matching."""
    match = re.search(rf"\b{re.escape(function_name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return ""

    start = match.end()
    depth = 1
    i = start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i]
        i += 1
    return ""


def count_hits(patterns, text: str) -> int:
    """Count how many structural evidence patterns appear in the source text."""
    hits = 0
    for pattern in patterns:
        if re.search(pattern, text):
            hits += 1
    return hits


code = strip_comments_and_strings(SRC.read_text(encoding="utf-8"))
fundamental_body = extract_function_body(code, "EstimateFundamental8Point")
essential_body = extract_function_body(code, "EstimateEssential8Point")

if not fundamental_body:
    print("Missing EstimateFundamental8Point body")
    sys.exit(1)

if not essential_body:
    print("Missing EstimateEssential8Point body")
    sys.exit(1)

normalization_patterns = [
    r"\bmean_[xy]\b",
    r"\bcentroid\b",
    r"sqrt\s*\(\s*2(?:\.0)?\s*\)",
    r"\bscale\b",
    r"\bT1\b",
    r"\bT2\b",
    r"transpose\s*\(\s*\)\s*\*.*\*",
]

normalization_hits = count_hits(normalization_patterns, code)
if normalization_hits < 3:
    print("Expected Hartley-style normalization evidence in src/geometry.cc")
    sys.exit(1)

# Essential matrix must enforce singular value constraint: two equal, one zero.
# Accept any reasonable variable name and multiple equivalent implementation patterns.
essential_constraint_patterns = [
    r"\w+\s*\(\s*0\s*\)\s*=\s*\w+\s*\(\s*1\s*\)",  # sigma(0) = sigma(1)
    r"\w+\s*\(\s*1\s*\)\s*=\s*\w+\s*\(\s*0\s*\)",  # sigma(1) = sigma(0)
    r"\w+\s*\[\s*0\s*\]\s*=\s*\w+\s*\[\s*1\s*\]",  # sigma[0] = sigma[1]
    r"\w+\s*\[\s*1\s*\]\s*=\s*\w+\s*\[\s*0\s*\]",  # sigma[1] = sigma[0]
    r"(?:Vector3d|Diagonal|DiagonalMatrix)\s*\(\s*1(?:\.0)?\s*,\s*1(?:\.0)?\s*,\s*0(?:\.0)?\s*\)",  # (1, 1, 0)
    r"\bJacobiSVD\b[\s\S]*?\bsingularValues\b",  # SVD with singular values access
    r"\bsingularValues\b.*=.*\b1(?:\.0)?\s*,\s*1(?:\.0)?\s*,\s*0(?:\.0)?",  # Direct singular value construction
    r"\b\w+\s*<<\s*\w+\s*,\s*\w+\s*,\s*0(?:\.0)?\b",  # s << sigma, sigma, 0.0
    r"\b\w+\s*=\s*0\.5\s*\*\s*\(\s*\w+\s*\(\s*0\s*\)\s*\+\s*\w+\s*\(\s*1\s*\)\s*\)",  # sigma = 0.5 * (s(0) + s(1))
]

essential_hits = count_hits(essential_constraint_patterns, code)
if essential_hits == 0:
    print("Expected essential-matrix singular value constraint handling in src/geometry.cc")
    sys.exit(1)

if "return Solve8Point" in essential_body and essential_hits == 0:
    print("Essential path appears to reuse the fundamental solve without essential-specific post-processing")
    sys.exit(1)

print("geometry structure checks passed")
