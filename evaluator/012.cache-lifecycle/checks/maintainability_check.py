from evaluator.shared.path_checks import (
    case_root_from_script,
    read_text,
)
from evaluator.shared.source_analysis import has_any_pattern
from evaluator.shared.check_output import emit_check_result

ROOT = case_root_from_script(__file__)
SRC = ROOT / "src"


def main() -> int:
    service_h = read_text(SRC / "inventory_report_service.h", missing_ok=False)
    service_cc = read_text(SRC / "inventory_report_service.cc", missing_ok=False)
    engine_h = read_text(SRC / "summary_engine.h", missing_ok=False)
    engine_cc = read_text(SRC / "summary_engine.cc", missing_ok=False)
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
    if has_any_pattern(static_patterns, service_cc) or has_any_pattern(
        static_patterns, engine_cc
    ):
        errors.append("Do not introduce global or static cached summary state")

    for bad_param in ["use_cache", "force_refresh", "cache_key", "bypass_cache"]:
        if bad_param in service_h:
            errors.append("Public API should not grow extra cache-control parameters")
            break

    if "ClearCache" not in service_h:
        errors.append("inventory_report_service.h must declare ClearCache()")

    if "Compute(" not in engine_h:
        errors.append("summary_engine.h must continue to expose Compute(...)")

    return emit_check_result(passed=not errors, findings=errors)


if __name__ == "__main__":
    raise SystemExit(main())
