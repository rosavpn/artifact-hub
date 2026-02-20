VERSION ?=
ARCH ?=

ifeq ($(strip $(VERSION)),)
$(error VERSION is required. Example: make VERSION=v1.0.8 ARCH=amd64)
endif

ifeq ($(strip $(ARCH)),)
$(error ARCH is required. Example: make VERSION=v1.0.8 ARCH=amd64)
endif

JOBS := $(shell getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)

WORK_ROOT := $(CURDIR)
BUILD_ROOT := $(WORK_ROOT)/.build
SRC_ROOT := $(BUILD_ROOT)/src
DIST_DIR := $(BUILD_ROOT)/dist
OUT_DIR ?= /out

WGHTTP_REPO := https://github.com/brsyuksel/wghttp.git
WGHTTP_SRC := wghttp
WGHTTP_LICENSE_URL := https://raw.githubusercontent.com/brsyuksel/wghttp/refs/tags/$(VERSION)/LICENSE

WGHTTP_APK_DEPS := \
	rustup

RUST_TARGET_amd64 := x86_64-unknown-linux-musl
RUST_TARGET_arm64 := aarch64-unknown-linux-musl
RUST_TARGET := $(RUST_TARGET_$(ARCH))

ifeq ($(strip $(RUST_TARGET)),)
$(error Unsupported ARCH '$(ARCH)'. Supported values: amd64 arm64)
endif

PACKAGE_NAME := wghttp-$(ARCH)
ARTIFACT_TARBALL := $(PACKAGE_NAME).tar.gz
METADATA_FILE := $(PACKAGE_NAME).metadata.json

prepare:
	@mkdir -p "$(SRC_ROOT)" "$(DIST_DIR)" "$(OUT_DIR)"

sys_deps:
	@apk add --no-cache $(WGHTTP_APK_DEPS)

get_source: prepare
	@cd "$(SRC_ROOT)" && \
		if [ ! -d "$(WGHTTP_SRC)/.git" ]; then git clone "$(WGHTTP_REPO)" "$(WGHTTP_SRC)"; fi
	@cd "$(SRC_ROOT)/$(WGHTTP_SRC)" && \
		git fetch --tags --force && \
		git checkout -f "$(VERSION)" && \
		git clean -fdx

dependencies: sys_deps
	@if command -v rustup >/dev/null 2>&1; then \
		rustup set profile minimal && \
		rustup toolchain install stable --target "$(RUST_TARGET)" --no-self-update; \
	elif command -v rustup-init >/dev/null 2>&1; then \
		rustup-init -y --profile minimal --default-toolchain stable --no-modify-path && \
		"$$HOME/.cargo/bin/rustup" target add "$(RUST_TARGET)"; \
	else \
		echo "rustup/rustup-init not found in container" >&2; \
		exit 1; \
	fi

compile: get_source dependencies
	@cd "$(SRC_ROOT)/$(WGHTTP_SRC)" && \
		if command -v cargo >/dev/null 2>&1; then \
			RUSTFLAGS="-C target-feature=+crt-static" cargo +stable build -j "$(JOBS)" --release --target "$(RUST_TARGET)" -p wghttp; \
		else \
			RUSTFLAGS="-C target-feature=+crt-static" "$$HOME/.cargo/bin/cargo" +stable build -j "$(JOBS)" --release --target "$(RUST_TARGET)" -p wghttp; \
		fi

dist: compile
	@rm -rf "$(DIST_DIR)"
	@mkdir -p "$(DIST_DIR)" "$(OUT_DIR)"
	@cp "$(SRC_ROOT)/$(WGHTTP_SRC)/target/$(RUST_TARGET)/release/wghttp" "$(DIST_DIR)/wghttp"
	@strip "$(DIST_DIR)/wghttp"
	@printf "%s\n" "$(VERSION)" > "$(DIST_DIR)/version"
	@wget -q -O "$(DIST_DIR)/LICENSE" "$(WGHTTP_LICENSE_URL)"
	@tar -czf "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" -C "$(DIST_DIR)" .
	@cp "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" "$(OUT_DIR)/$(ARTIFACT_TARBALL)"
	@TARBALL_SUM=$$(sha256sum "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" | awk '{print $$1}'); \
	WGHTTP_BIN_SHA256=$$(sha256sum "$(DIST_DIR)/wghttp" | awk '{print $$1}'); \
	printf '{"name":"wghttp","archive_file":"%s","archive_sum":"%s","version":"%s","arch":"%s","file_sums":{"wghttp":"%s"}}\n' \
	"$(ARTIFACT_TARBALL)" "$$TARBALL_SUM" "$(VERSION)" "$(ARCH)" "$$WGHTTP_BIN_SHA256" > "$(OUT_DIR)/$(METADATA_FILE)"
	@file "$(DIST_DIR)/wghttp"

clean:
	@rm -rf "$(BUILD_ROOT)"

all: dist

.PHONY: prepare sys_deps get_source dependencies compile dist clean all

