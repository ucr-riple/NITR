import os
import shutil
import subprocess
from pathlib import Path


DEFAULT_RUNTIME_ENV_VARS = (
    "OPENAI_API_KEY",
    "OPENAI_API_BASE",
    "NITR_GCP_PROJECT",
    "NITR_GCP_REGION",
    "NITR_VERTEX_ENDPOINT_ID",
    "NITR_VERTEX_ENDPOINT_LOCATION",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
)

PATH_LIKE_ENV_VARS = ("GOOGLE_APPLICATION_CREDENTIALS",)


def path_is_relative_to(path: Path, parent: Path) -> bool:
    """Backport Path.is_relative_to for simpler mount mapping."""
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def ensure_docker_cli():
    """Fail fast with a clear message when Docker is unavailable."""
    docker_path = shutil.which("docker")
    if docker_path is None:
        raise EnvironmentError(
            "Docker runtime requested but 'docker' was not found on PATH."
        )
    return docker_path


def run_streaming_command(cmd: list[str], cwd: Path) -> int:
    """Run one command while streaming stdout/stderr to the terminal."""
    print(f"[*] Running: {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)
    return completed.returncode


def build_docker_image(repo_root: Path, image: str, dockerfile: Path, platform: str):
    """Build a Docker image from the checked-out repository."""
    cmd = [
        "docker",
        "build",
        "--platform",
        platform,
        "-t",
        image,
        "-f",
        str(dockerfile),
        str(repo_root),
    ]
    exit_code = run_streaming_command(cmd, repo_root)
    if exit_code != 0:
        raise SystemExit(exit_code)


def parse_mount_spec(spec: str) -> tuple[Path, str]:
    """Parse host:container[:options] mount syntax."""
    parts = spec.split(":")
    if len(parts) < 2:
        raise ValueError(
            f"Invalid mount spec '{spec}'. Expected host_path:container_path[:options]."
        )
    host_path = Path(parts[0]).resolve()
    container_path = parts[1]
    suffix = f":{':'.join(parts[2:])}" if len(parts) > 2 else ""
    return host_path, f"{container_path}{suffix}"


def map_path_for_container(path: Path, mounts: list[tuple[Path, str]]) -> str:
    """Translate a host path into the matching container-visible path."""
    resolved = path.resolve()
    for host_root, container_root in mounts:
        normalized_container_root = container_root.split(":", 1)[0]
        if path_is_relative_to(resolved, host_root):
            relative = resolved.relative_to(host_root)
            if str(relative) == ".":
                return normalized_container_root
            return f"{normalized_container_root}/{relative.as_posix()}"
    raise ValueError(f"Path is not covered by any Docker mount: {resolved}")


def append_mount(
    docker_cmd: list[str],
    mounts: list[tuple[Path, str]],
    host_path: Path,
    container_path: str,
):
    """Register one bind mount both for docker run and host/container path mapping."""
    docker_cmd.extend(["-v", f"{host_path}:{container_path}"])
    mounts.append((host_path, container_path))


def collect_passthrough_env(args) -> list[str]:
    """Collect environment variables that should be injected into the container."""
    requested = list(DEFAULT_RUNTIME_ENV_VARS)
    requested.extend(args.pass_env or [])
    seen = set()
    env_names = []
    for name in requested:
        if not name or name in seen:
            continue
        seen.add(name)
        env_names.append(name)
    return env_names


def path_env_value_for_container(
    env_name: str,
    env_value: str,
    docker_cmd: list[str],
    mounts: list[tuple[Path, str]],
) -> str | None:
    """Map host file-backed env vars into the container and rewrite their values."""
    if env_name not in PATH_LIKE_ENV_VARS:
        return None

    host_path = Path(env_value).expanduser().resolve()
    if not host_path.exists():
        return None

    mount_root = host_path if host_path.is_dir() else host_path.parent
    if not any(path_is_relative_to(mount_root, mounted_root) for mounted_root, _ in mounts):
        container_root = f"/workspace/runtime-env/{env_name.lower()}"
        append_mount(docker_cmd, mounts, mount_root, f"{container_root}:ro")
    return map_path_for_container(host_path, mounts)


def add_environment_flags(
    docker_cmd: list[str], mounts: list[tuple[Path, str]], args
):
    """Inject host environment variables and optional env-files into docker run."""
    for env_file in args.docker_env_file or []:
        docker_cmd.extend(["--env-file", str(Path(env_file).resolve())])

    for env_name in collect_passthrough_env(args):
        env_value = os.environ.get(env_name)
        if env_value is None:
            continue
        container_value = path_env_value_for_container(
            env_name, env_value, docker_cmd, mounts
        )
        if container_value is not None:
            docker_cmd.extend(["-e", f"{env_name}={container_value}"])
            continue
        docker_cmd.extend(["-e", env_name])


def add_custom_mounts(
    docker_cmd: list[str], mounts: list[tuple[Path, str]], mount_specs: list[str] | None
):
    """Attach user-provided bind mounts to the container."""
    for spec in mount_specs or []:
        host_path, container_path = parse_mount_spec(spec)
        append_mount(docker_cmd, mounts, host_path, container_path)


def add_common_runtime_args(parser, *, default_dockerfile: str):
    """Register shared Docker runtime flags on a CLI parser."""
    parser.add_argument(
        "--runtime",
        choices=("local", "docker"),
        default="local",
        help="Execution runtime.",
    )
    parser.add_argument(
        "--docker-image",
        "--docker_image",
        dest="docker_image",
        default="nitr-linux-gcc:latest",
        help="Docker image to use when --runtime docker is selected.",
    )
    parser.add_argument(
        "--docker-platform",
        "--docker_platform",
        dest="docker_platform",
        default="linux/amd64",
        help="Docker platform to use when --runtime docker is selected.",
    )
    parser.add_argument(
        "--dockerfile",
        default=default_dockerfile,
        help="Dockerfile used by --docker_build.",
    )
    parser.add_argument(
        "--docker-build",
        "--docker_build",
        dest="docker_build",
        action="store_true",
        help="Build the Docker image before running when --runtime docker is selected.",
    )
    parser.add_argument(
        "--pass-env",
        action="append",
        dest="pass_env",
        default=[],
        help="Additional environment variable name to pass into Docker. Repeatable.",
    )
    parser.add_argument(
        "--docker-env-file",
        action="append",
        default=[],
        help="Path to a Docker env-file passed through to docker run. Repeatable.",
    )
    parser.add_argument(
        "--docker-mount",
        action="append",
        default=[],
        help="Extra bind mount in host_path:container_path[:options] form. Repeatable.",
    )


def docker_python_executable() -> str:
    """Return the Python executable name expected inside the runtime image."""
    return "python3"


def script_relpath(script_path: str) -> str:
    """Map one repository-local script path to a stable container path."""
    return Path(script_path).as_posix()


def exit_after_docker_run(
    *,
    args,
    repo_root: Path,
    script_path: str,
    forwarded_args: list[str],
    path_arg_names: set[str] | None = None,
    extra_mount_roots: list[Path] | None = None,
    extra_mount_specs: list[str] | None = None,
    pre_exec_shell_commands: list[str] | None = None,
):
    """Re-run the current script inside Docker and exit with the container status."""
    ensure_docker_cli()

    dockerfile = Path(args.dockerfile).resolve()
    if not dockerfile.is_file():
        raise FileNotFoundError(f"Dockerfile not found: {dockerfile}")

    if args.docker_build:
        build_docker_image(repo_root, args.docker_image, dockerfile, args.docker_platform)

    repo_mount = "/workspace/repo"
    mounts: list[tuple[Path, str]] = []
    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--platform",
        args.docker_platform,
        "-w",
        repo_mount,
    ]
    append_mount(docker_cmd, mounts, repo_root.resolve(), repo_mount)

    for extra_root in extra_mount_roots or []:
        resolved_root = extra_root.resolve()
        if any(path_is_relative_to(resolved_root, host_root) for host_root, _ in mounts):
            continue
        container_root = f"/workspace/mounts/{len(mounts)}"
        append_mount(docker_cmd, mounts, resolved_root, container_root)

    all_mount_specs = list(args.docker_mount or [])
    all_mount_specs.extend(extra_mount_specs or [])
    add_custom_mounts(docker_cmd, mounts, all_mount_specs)
    add_environment_flags(docker_cmd, mounts, args)

    mapped_args = []
    path_arg_names = path_arg_names or set()
    current_flag = None
    for value in forwarded_args:
        if current_flag in path_arg_names:
            mapped_args.append(map_path_for_container(Path(value).resolve(), mounts))
            current_flag = None
            continue

        mapped_args.append(value)
        current_flag = value if value.startswith("-") else None

    script_cmd = " ".join(
        [
            docker_python_executable(),
            script_relpath(script_path),
            "--runtime",
            "local",
            *(shlex_quote(arg) for arg in mapped_args),
        ]
    )
    if pre_exec_shell_commands:
        shell_cmd = " && ".join(pre_exec_shell_commands + [f"exec {script_cmd}"])
        container_cmd = ["bash", "-lc", shell_cmd]
    else:
        container_cmd = [
            docker_python_executable(),
            script_relpath(script_path),
            "--runtime",
            "local",
            *mapped_args,
        ]
    docker_cmd.extend([args.docker_image, *container_cmd])
    raise SystemExit(run_streaming_command(docker_cmd, repo_root))


def current_default_dockerfile() -> str:
    """Return the repository's default Dockerfile path."""
    return str(
        Path(__file__).resolve().parents[1] / "docker" / "nitr-linux-gcc.Dockerfile"
    )


def shlex_quote(value: str) -> str:
    """Shell-quote one argument for optional bash -lc wrapping."""
    return "'" + value.replace("'", "'\"'\"'") + "'"
