VERSION ?=
ARCH ?=

ifeq ($(strip $(VERSION)),)
$(error VERSION is required. Example: make VERSION=0.4.8.18 ARCH=amd64)
endif

ifeq ($(strip $(ARCH)),)
$(error ARCH is required. Example: make VERSION=0.4.8.18 ARCH=amd64)
endif

JOBS := $(shell getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)

WORK_ROOT := $(CURDIR)
BUILD_ROOT := $(WORK_ROOT)/.build
SRC_ROOT := $(BUILD_ROOT)/src
DIST_DIR := $(BUILD_ROOT)/dist
OUT_DIR ?= /out
TOR_INSTALL_PREFIX := $(BUILD_ROOT)/tor-install

TOR_VERSION := $(patsubst tor-%,%,$(VERSION))
TOR_SRC := tor-$(TOR_VERSION)
TOR_TARBALL := $(TOR_SRC).tar.gz
TOR_URL := https://dist.torproject.org/$(TOR_TARBALL)
TOR_LICENSE_URL := https://gitlab.torproject.org/tpo/core/tor/-/raw/$(VERSION)/LICENSE

TOR_APK_DEPS := \
	openssl-dev \
	openssl-libs-static \
	libevent-dev \
	libevent-static \
	zlib-dev \
	zlib-static

PACKAGE_NAME := tor-$(ARCH)
ARTIFACT_TARBALL := $(PACKAGE_NAME).tar.gz
METADATA_FILE := $(PACKAGE_NAME).metadata.json

prepare:
	@mkdir -p "$(SRC_ROOT)" "$(DIST_DIR)" "$(OUT_DIR)"

sys_deps:
	@apk add --no-cache $(TOR_APK_DEPS)

get_source: prepare
	@cd "$(SRC_ROOT)" && \
		if [ ! -f "$(TOR_TARBALL)" ]; then wget -q "$(TOR_URL)"; fi
	@cd "$(SRC_ROOT)" && rm -rf "$(TOR_SRC)" && tar -xzf "$(TOR_TARBALL)"

dependencies: sys_deps

compile: get_source dependencies
	@cd "$(SRC_ROOT)/$(TOR_SRC)" && \
		CPPFLAGS="" \
		LDFLAGS="-static" \
		PKG_CONFIG="pkg-config --static" \
		./configure \
			--prefix="$(TOR_INSTALL_PREFIX)" \
			--disable-asciidoc \
			--disable-systemd \
			--disable-seccomp \
			--disable-lzma \
			--disable-zstd \
			--enable-static-tor \
			--with-openssl-dir=/usr \
			--with-libevent-dir=/usr \
			--with-zlib-dir=/usr && \
		make -j"$(JOBS)" && \
		make install

dist: compile
	@rm -rf "$(DIST_DIR)"
	@mkdir -p "$(DIST_DIR)" "$(OUT_DIR)"
	@cp "$(TOR_INSTALL_PREFIX)/bin/tor" "$(DIST_DIR)/tor"
	@strip "$(DIST_DIR)/tor"
	@printf "%s\n" "$(TOR_VERSION)" > "$(DIST_DIR)/version"
	@wget -q -O "$(DIST_DIR)/LICENSE" "$(TOR_LICENSE_URL)"
	@tar -czf "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" -C "$(DIST_DIR)" .
	@cp "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" "$(OUT_DIR)/$(ARTIFACT_TARBALL)"
	@TARBALL_SUM=$$(sha256sum "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" | awk '{print $$1}'); \
	TOR_BIN_SHA256=$$(sha256sum "$(DIST_DIR)/tor" | awk '{print $$1}'); \
	printf '{"name":"tor","archive_file":"%s","archive_sum":"%s","version":"%s","arch":"%s","file_sums":{"tor":"%s"}}\n' \
	"$(ARTIFACT_TARBALL)" "$$TARBALL_SUM" "$(TOR_VERSION)" "$(ARCH)" "$$TOR_BIN_SHA256" > "$(OUT_DIR)/$(METADATA_FILE)"
	@file "$(DIST_DIR)/tor"

clean:
	@rm -rf "$(BUILD_ROOT)"

all: dist

.PHONY: prepare sys_deps get_source dependencies compile dist clean all