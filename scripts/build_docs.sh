#!/usr/bin/env bash
set -e

# Change to repository root
cd "$(dirname "$0")/.."

echo "Generating API documentation stubs..."
sphinx-apidoc -f -o docs/source clara/

echo "Building HTML documentation..."
sphinx-build -b html "$@" docs/source docs/build/html

echo "Documentation built successfully in docs/build/html/"
