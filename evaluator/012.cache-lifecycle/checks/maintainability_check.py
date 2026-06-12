from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluator.shared.check_utils import case_root_from_script

ROOT = case_root_from_script(__file__)
SRC = ROOT / "src"
service_h = (SRC / "inventory_report_service.h").read_text()
service_cc = (SRC / "inventory_report_service.cc").read_text()
engine_h = (SRC / "summary_engine.h").read_text()
engine_cc = (SRC / "summary_engine.cc").read_text()

errors = []

engine_all = engine_h + "\n" + engine_cc
for banned in ["cache", "cached", "last_summary", "last_products"]:
    if banned in engine_all.lower():
        errors.append(
            "SummaryEngine should remain a pure computation dependency and must not own cache state"
        )
        break

static_patterns = [
    r"static\s+.*InventorySummary",
    r"static\s+std::vector\s*<\s*Product\s*>",
    r"static\s+auto\s+.*summary",
]
for pattern in static_patterns:
    if re.search(pattern, service_cc) or re.search(pattern, engine_cc):
        errors.append("Do not introduce global or static cached summary state")
        break

for bad_param in ["use_cache", "force_refresh", "cache_key", "bypass_cache"]:
    if bad_param in service_h:
        errors.append("Public API should not grow extra cache-control parameters")
        break

if "ClearCache" not in service_h:
    errors.append("inventory_report_service.h must declare ClearCache()")

if "Compute(" not in engine_h:
    errors.append("summary_engine.h must continue to expose Compute(...)")

if errors:
    for error in errors:
        print(error)
    sys.exit(1)
