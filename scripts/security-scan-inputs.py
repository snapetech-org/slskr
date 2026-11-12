#!/usr/bin/env python3
"""Detect applicable security-scan inputs from the current Git checkout.

Use Git's NUL-delimited file list so scan selection does not silently depend on
optional utilities such as ripgrep being installed on a CI runner.
"""

from __future__ import annotations

import fnmatch
import os
import subprocess
import sys
from pathlib import PurePosixPath


DEPENDENCY_PATTERNS = (
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock*",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "pyproject.toml",
    "requirements*.txt",
    "uv.lock",
    "poetry.lock",
    "Pipfile*",
    "*.csproj",
    "*.sln",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "gradle.lockfile",
    "Gemfile*",
    "composer.json",
    "composer.lock",
    "mix.lock",
    "pubspec.yaml",
)

SOURCE_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".kts",
    ".cs",
    ".c",
    ".h",
    ".cc",
    ".cpp",
    ".hpp",
    ".php",
    ".rb",
    ".swift",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".sql",
    ".scala",
    ".ex",
    ".exs",
    ".tf",
    ".yml",
    ".yaml",
}

EXCLUDED_SOURCE_PATHS = {
    "scripts/install-security-hooks.sh",
    "scripts/security-scan-local.sh",
    "scripts/update-security-tools.sh",
}


def checkout_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [
        path
        for raw_path in result.stdout.split(b"\0")
        if raw_path
        and os.path.isfile(path := os.fsdecode(raw_path))
    ]


def is_dependency_file(path: str) -> bool:
    return any(
        fnmatch.fnmatchcase(PurePosixPath(path).name, pattern)
        for pattern in DEPENDENCY_PATTERNS
    )


def is_iac_file(path: str) -> bool:
    parsed = PurePosixPath(path)
    name = parsed.name
    parts = parsed.parts
    if name == "Dockerfile" or name.startswith("Dockerfile."):
        return True
    if name.startswith(("docker-compose", "compose")) and parsed.suffix in {
        ".yml",
        ".yaml",
    }:
        return True
    if parsed.suffix in {".tf", ".tfvars"} or name in {
        "Chart.yaml",
        "kustomization.yaml",
    }:
        return True
    if (
        len(parts) > 1
        and parts[0] == ".github"
        and parts[1] == "workflows"
        and parsed.suffix in {".yml", ".yaml"}
    ):
        return True
    return (
        len(parts) > 1
        and parts[0] in {"k8s", "helm", "charts", "deploy", "infra"}
        and parsed.suffix in {".yml", ".yaml"}
    )


def is_source_file(path: str) -> bool:
    parsed = PurePosixPath(path)
    if path in EXCLUDED_SOURCE_PATHS:
        return False
    if any(part in {"docs", ".githooks", ".husky"} for part in parsed.parts):
        return False
    name = parsed.name
    return (
        parsed.suffix in SOURCE_SUFFIXES
        or name == "Dockerfile"
        or name.startswith("Dockerfile.")
        or (
            name.startswith(("docker-compose", "compose"))
            and parsed.suffix in {".yml", ".yaml"}
        )
    )


def trivy_scanners(files: list[str]) -> list[str]:
    scanners: list[str] = []
    if any(is_dependency_file(path) for path in files):
        scanners.append("vuln")
    if any(is_iac_file(path) for path in files):
        scanners.append("misconfig")
    if scanners or any(is_source_file(path) for path in files):
        scanners.append("secret")
    return scanners


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"semgrep", "trivy"}:
        print("usage: security-scan-inputs.py semgrep|trivy", file=sys.stderr)
        return 2
    try:
        files = checkout_files()
    except OSError as error:
        print(f"security scan input discovery failed: {error}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as error:
        details = os.fsdecode(error.stderr or b"").strip()
        message = f"security scan input discovery failed: {error}"
        if details:
            message += f": {details}"
        print(message, file=sys.stderr)
        return 2

    if sys.argv[1] == "semgrep":
        return 0 if any(is_source_file(path) for path in files) else 1

    print(",".join(trivy_scanners(files)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
