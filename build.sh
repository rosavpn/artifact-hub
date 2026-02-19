#!/bin/sh

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
DOCKERFILE_PATH="$SCRIPT_DIR/Dockerfile"

if ! command -v docker >/dev/null 2>&1; then
	echo "Error: docker command is not available on this system." >&2
	exit 1
fi

if [ ! -f "$DOCKERFILE_PATH" ]; then
	echo "Error: Dockerfile not found at $DOCKERFILE_PATH" >&2
	exit 1
fi

if [ "$#" -ne 3 ]; then
	echo "Usage: $0 <package_name> <version> <arch>" >&2
	exit 1
fi

PACKAGE_NAME="$1"
VERSION="$2"
ARCH="$3"

if [ -z "$PACKAGE_NAME" ] || [ -z "$VERSION" ] || [ -z "$ARCH" ]; then
	echo "Error: package name, version, and architecture are required." >&2
	exit 1
fi

RECIPE_FILE="$SCRIPT_DIR/packages/$PACKAGE_NAME/Makefile"
if [ ! -f "$RECIPE_FILE" ]; then
	echo "Error: recipe file not found at $RECIPE_FILE" >&2
	exit 1
fi

OUT_DIR="$SCRIPT_DIR/out"
mkdir -p "$OUT_DIR"

TEMP_IMAGE_TAG="artifact-builder:$PACKAGE_NAME-$VERSION-$ARCH-$$"

cleanup() {
	docker image rm -f "$TEMP_IMAGE_TAG" >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

echo "Building Docker image from Dockerfile..."
docker build -f "$DOCKERFILE_PATH" -t "$TEMP_IMAGE_TAG" "$SCRIPT_DIR"

echo "Running package recipe..."
docker run --rm \
	-v "$RECIPE_FILE:/build/Makefile:ro" \
	-v "$OUT_DIR:/out" \
	"$TEMP_IMAGE_TAG" \
	make -f /build/Makefile all VERSION="$VERSION" ARCH="$ARCH" OUT_DIR=/out

echo "Build job completed. Output directory: $OUT_DIR"
