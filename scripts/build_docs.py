#!/usr/bin/env python3
"""Build Sphinx documentation for clara-core."""

import argparse
import subprocess
import sys
from pathlib import Path


def build_docs(strict: bool = False) -> int:
    """Generate API stubs and build Sphinx HTML documentation.

    Args:
        strict: If True, treat warnings as errors during sphinx-build.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    repo_root = Path(__file__).resolve().parent.parent
    source_dir = repo_root / "docs" / "source"
    build_dir = repo_root / "docs" / "build" / "html"
    package_dir = repo_root / "clara"

    # Step 1: Run sphinx-apidoc
    apidoc_cmd = [
        sys.executable,
        "-m",
        "sphinx.ext.apidoc",
        "-f",
        "-o",
        str(source_dir),
        str(package_dir),
    ]
    print(f"Generating API documentation stubs: {' '.join(apidoc_cmd)}")
    apidoc_res = subprocess.run(apidoc_cmd, cwd=repo_root)
    if apidoc_res.returncode != 0:
        print("Error: sphinx-apidoc failed.", file=sys.stderr)
        return apidoc_res.returncode

    # Step 2: Run sphinx-build
    sphinx_build_cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "-b",
        "html",
    ]
    if strict:
        sphinx_build_cmd.extend(["-W", "--keep-going"])
    sphinx_build_cmd.extend([str(source_dir), str(build_dir)])

    print(f"Building HTML documentation: {' '.join(sphinx_build_cmd)}")
    build_res = subprocess.run(sphinx_build_cmd, cwd=repo_root)
    if build_res.returncode != 0:
        print("Error: sphinx-build failed.", file=sys.stderr)
        return build_res.returncode

    print(
        f"\nDocumentation built successfully! Open {build_dir / 'index.html'} to view."
    )
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Build clara-core Sphinx documentation."
    )
    parser.add_argument(
        "-W",
        "--strict",
        action="store_true",
        help="Turn warnings into errors to ensure strict documentation quality.",
    )
    args = parser.parse_args()
    sys.exit(build_docs(strict=args.strict))


if __name__ == "__main__":
    main()
