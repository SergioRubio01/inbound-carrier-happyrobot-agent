#!/usr/bin/env python3
"""Version management script for HappyRobot FDE."""

import re
import sys
from pathlib import Path
from typing import Optional, Tuple


def parse_version(version: str) -> Tuple[int, int, int, Optional[str]]:
    """Parse semantic version string."""
    match = re.match(r"^v?(\d+)\.(\d+)\.(\d+)(?:-(.+))?$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")

    major, minor, patch, prerelease = match.groups()
    return int(major), int(minor), int(patch), prerelease


def format_version(
    major: int, minor: int, patch: int, prerelease: Optional[str] = None
) -> str:
    """Format version components into semantic version string."""
    version = f"{major}.{minor}.{patch}"
    if prerelease:
        version += f"-{prerelease}"
    return version


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    with open(pyproject_path, "r") as f:
        content = f.read()

    match = re.search(r'^version = "(.+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Version not found in pyproject.toml")

    return match.group(1)


def update_version(new_version: str) -> None:
    """Update version in pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    with open(pyproject_path, "r") as f:
        content = f.read()

    content = re.sub(
        r'^version = ".+"',
        f'version = "{new_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )

    with open(pyproject_path, "w") as f:
        f.write(content)

    print(f"Updated version to {new_version} in pyproject.toml")


def bump_version(bump_type: str, prerelease: Optional[str] = None) -> str:
    """Bump version based on type."""
    current = get_current_version()
    major, minor, patch, current_pre = parse_version(current)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    elif bump_type == "prerelease":
        if current_pre:
            # Increment prerelease version
            pre_parts = current_pre.split(".")
            if len(pre_parts) == 2 and pre_parts[1].isdigit():
                pre_parts[1] = str(int(pre_parts[1]) + 1)
                prerelease = ".".join(pre_parts)
            else:
                patch += 1
                prerelease = prerelease or "rc.1"
        else:
            patch += 1
            prerelease = prerelease or "rc.1"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    new_version = format_version(major, minor, patch, prerelease)
    return new_version


def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Version management for HappyRobot FDE"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Get current version
    subparsers.add_parser("get", help="Get current version")

    # Set version
    set_parser = subparsers.add_parser("set", help="Set version")
    set_parser.add_argument("version", help="New version (e.g., 1.2.3)")

    # Bump version
    bump_parser = subparsers.add_parser("bump", help="Bump version")
    bump_parser.add_argument(
        "type",
        choices=["major", "minor", "patch", "prerelease"],
        help="Type of version bump",
    )
    bump_parser.add_argument(
        "--prerelease", help="Prerelease identifier (e.g., alpha, beta, rc)"
    )

    args = parser.parse_args()

    if args.command == "get":
        print(get_current_version())
    elif args.command == "set":
        update_version(args.version)
    elif args.command == "bump":
        new_version = bump_version(args.type, args.prerelease)
        update_version(new_version)
        print(new_version)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
