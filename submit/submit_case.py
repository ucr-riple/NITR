import argparse
from pathlib import Path

from backends import BACKEND_RUNNERS
from docker_runtime import (
    add_common_runtime_args,
    current_default_dockerfile,
    exit_after_docker_run,
)

DEFAULT_CODEX_DOCKER_IMAGE = "nitr-linux-gcc-codex:latest"


def current_codex_dockerfile() -> str:
    """Return the repository's default Codex-enabled Dockerfile path."""
    return str(
        Path(__file__).resolve().parents[1]
        / "docker"
        / "nitr-linux-gcc-codex.Dockerfile"
    )


def codex_auth_mount_specs() -> list[str]:
    """Build minimal read-only Codex auth mounts when available on the host."""
    codex_home = Path.home() / ".codex"
    mount_specs = []
    for filename in ("auth.json", "config.toml"):
        host_path = codex_home / filename
        if host_path.is_file():
            mount_specs.append(f"{host_path.resolve()}:/root/.codex/{filename}:ro")
    return mount_specs


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
        "--input-dir",
        "--input_dir",
        "-i",
        dest="input_dir",
        default=".",
        help="Repo root or cases root",
    )
    parser.add_argument(
        "--output-dir",
        "--output_dir",
        "-o",
        dest="output_dir",
        default="./output",
        help="Root directory for generated case outputs",
    )
    parser.add_argument(
        "--case-id",
        "--case_id",
        "-c",
        dest="case_id",
        required=True,
        help="Three-digit case id, e.g. 001",
    )

    parser.add_argument(
        "--model-name",
        "--model_name",
        dest="model_name",
        help="Optional model override for supported backends",
    )
    parser.add_argument(
        "--project-id",
        "--project_id",
        dest="project_id",
        help="Optional project id override",
    )
    parser.add_argument("--region", help="Optional region override")
    parser.add_argument(
        "--endpoint-id",
        "--endpoint_id",
        dest="endpoint_id",
        help="Optional endpoint id override",
    )
    parser.add_argument(
        "--endpoint-location",
        "--endpoint_location",
        dest="endpoint_location",
        help="Optional endpoint location override",
    )
    parser.add_argument(
        "--start-step",
        "--start_step",
        dest="start_step",
        type=int,
        help="Optional first step for multi-step capable backends",
    )
    parser.add_argument(
        "--end-step",
        "--end_step",
        dest="end_step",
        type=int,
        help="Optional last step for multi-step capable backends",
    )
    add_common_runtime_args(parser, default_dockerfile=current_default_dockerfile())
    return parser


def main():
    """Parse CLI arguments and hand execution to the selected backend runner."""
    parser = build_parser()
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    if args.runtime == "docker":
        extra_mount_specs = []
        pre_exec_shell_commands = []

        if args.backend == "chatgpt-codex":
            if (
                args.docker_image == "nitr-linux-gcc:latest"
                and args.dockerfile == current_default_dockerfile()
            ):
                args.docker_image = DEFAULT_CODEX_DOCKER_IMAGE
                args.dockerfile = current_codex_dockerfile()
            extra_mount_specs = codex_auth_mount_specs()
            pre_exec_shell_commands = ["mkdir -p /root/.codex"]

        input_mount_root = Path(args.input_dir).resolve()
        output_mount_root = Path(args.output_dir).resolve()
        if not output_mount_root.exists():
            output_mount_root = output_mount_root.parent

        forwarded_args = [
            "--backend",
            args.backend,
            "--input-dir",
            str(Path(args.input_dir).resolve()),
            "--output-dir",
            str(Path(args.output_dir).resolve()),
            "--case-id",
            args.case_id,
        ]
        if args.model_name:
            forwarded_args.extend(["--model-name", args.model_name])
        if args.project_id:
            forwarded_args.extend(["--project-id", args.project_id])
        if args.region:
            forwarded_args.extend(["--region", args.region])
        if args.endpoint_id:
            forwarded_args.extend(["--endpoint-id", args.endpoint_id])
        if args.endpoint_location:
            forwarded_args.extend(["--endpoint-location", args.endpoint_location])
        if args.start_step is not None:
            forwarded_args.extend(["--start-step", str(args.start_step)])
        if args.end_step is not None:
            forwarded_args.extend(["--end-step", str(args.end_step)])

        extra_mount_roots = [
            input_mount_root,
            output_mount_root,
        ]
        exit_after_docker_run(
            args=args,
            repo_root=repo_root,
            script_path="submit/submit_case.py",
            forwarded_args=forwarded_args,
            path_arg_names={"--input-dir", "--output-dir"},
            extra_mount_roots=extra_mount_roots,
            extra_mount_specs=extra_mount_specs,
            pre_exec_shell_commands=pre_exec_shell_commands,
        )

    print(f"[*] Dispatching backend '{args.backend}'")
    BACKEND_RUNNERS[args.backend](args)


if __name__ == "__main__":
    main()
