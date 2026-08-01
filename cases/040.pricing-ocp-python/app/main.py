from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.pricing import Order, compute_final_price


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input_path", required=True)
    parser.add_argument("--out", dest="output_path", required=True)
    parser.add_argument("--milestone", required=True)
    parser.add_argument("--rules")
    args = parser.parse_args()

    milestones = {"m1": 1, "m2": 2, "m3": 3, "m4": 4}
    if args.milestone not in milestones:
        print("ERR_UNSUPPORTED_MILESTONE", file=sys.stderr)
        return 1

    try:
        payload = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
        order = Order(
            subtotal_cents=round(float(payload["subtotal"]) * 100),
            is_member=payload["is_member"],
            items=payload["items"],
            coupons=tuple(payload.get("coupons", [])),
        )
        result = compute_final_price(order, milestones[args.milestone])
        Path(args.output_path).write_text(
            json.dumps(
                {
                    "final_price": result.final_price_cents / 100,
                    "applied_rules": result.applied_rules,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        print("ERR_INVALID_JSON", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
