import argparse

from backends import BACKEND_RUNNERS


def build_parser():
    """Build the shared CLI for dispatching one case to a backend implementation."""
    parser = argparse.ArgumentParser(
        description="Unified NITR submit entrypoint across supported backends."
    )
    parser.add_argument(
        "--backend",
        required=True,
        choices=sorted(BACKEND_RUNNERS.keys()),
        help="Submission backend to use.",
    )
    parser.add_argument(
        "--input_dir", "-i", default=".", help="Repo root or cases root"
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        default="./output",
        help="Root directory for generated case outputs",
    )
    parser.add_argument(
        "--case_id", "-c", required=True, help="Three-digit case id, e.g. 001"
    )

    parser.add_argument(
        "--model_name", help="Optional model override for supported backends"
    )
    parser.add_argument("--project_id", help="Optional project id override")
    parser.add_argument("--region", help="Optional region override")
    parser.add_argument("--endpoint_id", help="Optional endpoint id override")
    parser.add_argument(
        "--endpoint_location", help="Optional endpoint location override"
    )
    parser.add_argument(
        "--start_step",
        type=int,
        help="Optional first step for multi-step capable backends",
    )
    parser.add_argument(
        "--end_step",
        type=int,
        help="Optional last step for multi-step capable backends",
    )
    return parser


def main():
    """Parse CLI arguments and hand execution to the selected backend runner."""
    parser = build_parser()
    args = parser.parse_args()

    print(f"[*] Dispatching backend '{args.backend}'")
    BACKEND_RUNNERS[args.backend](args)


if __name__ == "__main__":
    main()
