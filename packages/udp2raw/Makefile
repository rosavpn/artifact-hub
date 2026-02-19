VERSION ?=
ARCH ?=

ifeq ($(strip $(VERSION)),)
$(error VERSION is required. Example: make VERSION=20230206.0 ARCH=amd64)
endif

ifeq ($(strip $(ARCH)),)
$(error ARCH is required. Example: make VERSION=20230206.0 ARCH=amd64)
endif

JOBS := $(shell getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)

WORK_ROOT := $(CURDIR)
BUILD_ROOT := $(WORK_ROOT)/.build
SRC_ROOT := $(BUILD_ROOT)/src
DIST_DIR := $(BUILD_ROOT)/dist
OUT_DIR ?= /out

UDP2RAW_SRC := udp2raw-$(VERSION)
UDP2RAW_TARBALL := $(VERSION).tar.gz
UDP2RAW_URL := https://github.com/wangyu-/udp2raw/archive/refs/tags/$(UDP2RAW_TARBALL)

PACKAGE_NAME := udp2raw-$(ARCH)
ARTIFACT_TARBALL := $(PACKAGE_NAME).tar.gz
METADATA_FILE := $(PACKAGE_NAME).metadata.json

prepare:
	@mkdir -p "$(SRC_ROOT)" "$(DIST_DIR)" "$(OUT_DIR)"

sys_deps:
	@apk add --no-cache libstdc++

get_source: prepare
	@cd "$(SRC_ROOT)" && \
		if [ ! -f "$(UDP2RAW_TARBALL)" ]; then wget -q "$(UDP2RAW_URL)" -O "$(UDP2RAW_TARBALL)"; fi
	@cd "$(SRC_ROOT)" && rm -rf "$(UDP2RAW_SRC)" && tar -xzf "$(UDP2RAW_TARBALL)"

dependencies: sys_deps

compile: get_source dependencies
	@cd "$(SRC_ROOT)/$(UDP2RAW_SRC)" && \
		make -j"$(JOBS)" all

dist: compile
	@rm -rf "$(DIST_DIR)"
	@mkdir -p "$(DIST_DIR)" "$(OUT_DIR)"
	@cp "$(SRC_ROOT)/$(UDP2RAW_SRC)/udp2raw" "$(DIST_DIR)/udp2raw"
	@strip "$(DIST_DIR)/udp2raw"
	@printf "%s\n" "$(VERSION)" > "$(DIST_DIR)/version"
	@tar -czf "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" -C "$(DIST_DIR)" .
	@cp "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" "$(OUT_DIR)/$(ARTIFACT_TARBALL)"
	@TARBALL_SUM=$$(sha256sum "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" | awk '{print $$1}'); \
	UDP2RAW_BIN_SHA256=$$(sha256sum "$(DIST_DIR)/udp2raw" | awk '{print $$1}'); \
	printf '{"name":"udp2raw","archive_file":"%s","archive_sum":"%s","version":"%s","arch":"%s","file_sums":{"udp2raw":"%s"}}\n' \
	"$(ARTIFACT_TARBALL)" "$$TARBALL_SUM" "$(VERSION)" "$(ARCH)" "$$UDP2RAW_BIN_SHA256" > "$(OUT_DIR)/$(METADATA_FILE)"
	@file "$(DIST_DIR)/udp2raw"

clean:
	@rm -rf "$(BUILD_ROOT)"

all: dist

.PHONY: prepare sys_deps get_source dependencies compile dist clean all
