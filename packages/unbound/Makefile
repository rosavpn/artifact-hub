VERSION ?=
ARCH ?=

ifeq ($(strip $(VERSION)),)
$(error VERSION is required. Example: make VERSION=release-1.22.0 ARCH=amd64)
endif

ifeq ($(strip $(ARCH)),)
$(error ARCH is required. Example: make VERSION=release-1.22.0 ARCH=amd64)
endif

JOBS := $(shell getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)

WORK_ROOT := $(CURDIR)
BUILD_ROOT := $(WORK_ROOT)/.build
SRC_ROOT := $(BUILD_ROOT)/src
DIST_DIR := $(BUILD_ROOT)/dist
OUT_DIR ?= /out
UNBOUND_INSTALL_PREFIX := $(BUILD_ROOT)/unbound-install

UNBOUND_REPO := https://github.com/NLnetLabs/unbound.git
UNBOUND_SRC := unbound
UNBOUND_LICENSE_URL := https://raw.githubusercontent.com/NLnetLabs/unbound/refs/tags/$(VERSION)/LICENSE

UNBOUND_APK_DEPS := \
	openssl-dev \
	openssl-libs-static \
	libevent-dev \
	libevent-static \
	expat-dev \
	expat-static \
	zlib-dev \
	zlib-static \
	zstd-dev \
	zstd-static

PACKAGE_NAME := unbound-$(ARCH)
ARTIFACT_TARBALL := $(PACKAGE_NAME).tar.gz
METADATA_FILE := $(PACKAGE_NAME).metadata.json

prepare:
	@mkdir -p "$(SRC_ROOT)" "$(DIST_DIR)" "$(OUT_DIR)"

sys_deps:
	@apk add --no-cache $(UNBOUND_APK_DEPS)

get_source: prepare
	@cd "$(SRC_ROOT)" && \
		if [ ! -d "$(UNBOUND_SRC)/.git" ]; then git clone "$(UNBOUND_REPO)" "$(UNBOUND_SRC)"; fi
	@cd "$(SRC_ROOT)/$(UNBOUND_SRC)" && \
		git fetch --tags --force && \
		git checkout -f "$(VERSION)" && \
		git clean -fdx

dependencies: sys_deps

compile: get_source dependencies
	@cd "$(SRC_ROOT)/$(UNBOUND_SRC)" && \
		if [ -x ./autogen.sh ] && [ ! -x ./configure ]; then ./autogen.sh; fi && \
		CFLAGS="-O2 -static -fno-pie" \
		CPPFLAGS="-I/usr/include" \
		LDFLAGS="-static -no-pie -L/usr/lib" \
		PKG_CONFIG="pkg-config --static" \
		./configure \
			--prefix="$(UNBOUND_INSTALL_PREFIX)" \
			--disable-shared \
			--enable-static-exe \
			--with-ssl=/usr \
			--with-libevent=/usr \
			--without-pythonmodule && \
		make -j"$(JOBS)" staticexe=-all-static && \
		make staticexe=-all-static install

smoke_test: compile
	@"$(UNBOUND_INSTALL_PREFIX)/sbin/unbound" -V >/dev/null

dist: smoke_test
	@rm -rf "$(DIST_DIR)"
	@mkdir -p "$(DIST_DIR)" "$(OUT_DIR)"
	@if [ -f "$(UNBOUND_INSTALL_PREFIX)/sbin/unbound" ]; then cp "$(UNBOUND_INSTALL_PREFIX)/sbin/unbound" "$(DIST_DIR)/unbound"; fi
	@if [ -f "$(UNBOUND_INSTALL_PREFIX)/sbin/unbound-checkconf" ]; then cp "$(UNBOUND_INSTALL_PREFIX)/sbin/unbound-checkconf" "$(DIST_DIR)/unbound-checkconf"; fi
	@if [ -f "$(UNBOUND_INSTALL_PREFIX)/sbin/unbound-control" ]; then cp "$(UNBOUND_INSTALL_PREFIX)/sbin/unbound-control" "$(DIST_DIR)/unbound-control"; fi
	@if [ -f "$(UNBOUND_INSTALL_PREFIX)/bin/unbound-host" ]; then cp "$(UNBOUND_INSTALL_PREFIX)/bin/unbound-host" "$(DIST_DIR)/unbound-host"; fi
	@if [ -f "$(UNBOUND_INSTALL_PREFIX)/bin/unbound-anchor" ]; then cp "$(UNBOUND_INSTALL_PREFIX)/bin/unbound-anchor" "$(DIST_DIR)/unbound-anchor"; fi
	@if [ -f "$(DIST_DIR)/unbound" ]; then strip "$(DIST_DIR)/unbound"; fi
	@if [ -f "$(DIST_DIR)/unbound-checkconf" ]; then strip "$(DIST_DIR)/unbound-checkconf"; fi
	@if [ -f "$(DIST_DIR)/unbound-control" ]; then strip "$(DIST_DIR)/unbound-control"; fi
	@if [ -f "$(DIST_DIR)/unbound-host" ]; then strip "$(DIST_DIR)/unbound-host"; fi
	@if [ -f "$(DIST_DIR)/unbound-anchor" ]; then strip "$(DIST_DIR)/unbound-anchor"; fi
	@printf "%s\n" "$(VERSION)" > "$(DIST_DIR)/version"
	@wget -q -O "$(DIST_DIR)/LICENSE" "$(UNBOUND_LICENSE_URL)"
	@tar -czf "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" -C "$(DIST_DIR)" .
	@cp "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" "$(OUT_DIR)/$(ARTIFACT_TARBALL)"
	@TARBALL_SUM=$$(sha256sum "$(BUILD_ROOT)/$(ARTIFACT_TARBALL)" | awk '{print $$1}'); \
	UNBOUND_BIN_SHA256=$$(sha256sum "$(DIST_DIR)/unbound" | awk '{print $$1}'); \
	UNBOUND_CHECKCONF_SHA256=$$(if [ -f "$(DIST_DIR)/unbound-checkconf" ]; then sha256sum "$(DIST_DIR)/unbound-checkconf" | awk '{print $$1}'; else printf ""; fi); \
	UNBOUND_CONTROL_SHA256=$$(if [ -f "$(DIST_DIR)/unbound-control" ]; then sha256sum "$(DIST_DIR)/unbound-control" | awk '{print $$1}'; else printf ""; fi); \
	printf '{"name":"unbound","archive_file":"%s","archive_sum":"%s","version":"%s","arch":"%s","file_sums":{"unbound":"%s","unbound-checkconf":"%s","unbound-control":"%s"}}\n' \
	"$(ARTIFACT_TARBALL)" "$$TARBALL_SUM" "$(VERSION)" "$(ARCH)" "$$UNBOUND_BIN_SHA256" "$$UNBOUND_CHECKCONF_SHA256" "$$UNBOUND_CONTROL_SHA256" > "$(OUT_DIR)/$(METADATA_FILE)"
	@file "$(DIST_DIR)/unbound"

clean:
	@rm -rf "$(BUILD_ROOT)"

all: dist

.PHONY: prepare sys_deps get_source dependencies compile smoke_test dist clean all
