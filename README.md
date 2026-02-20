# artifact-hub

Build static package artifacts with musl in an Alpine-based Docker environment.

This repository provides:
- a shared Docker build environment (`Dockerfile`)
- a package runner (`build.sh`)
- per-package recipe Makefiles under `packages/<name>/Makefile`
- version tracking and updater (`versions.json`, `update_versions.py`)

Each recipe is responsible for fetching source, installing package-specific deps, building statically, and exporting artifacts to `/out` (mapped to host `out/`).

## Requirements

- Docker
- POSIX shell (`sh`)

## Repository layout

```text
.
├── Dockerfile
├── build.sh
├── update_versions.py
├── versions.json
├── packages/
│   ├── tor/
│   │   └── Makefile
│   ├── udp2raw/
│   │   └── Makefile
│   ├── unbound/
│   │   └── Makefile
│   └── wghttp/
│       └── Makefile
└── out/                    # generated on demand
```

## How it works

`build.sh` takes 3 parameters:

```sh
./build.sh <package_name> <version> <arch>
```

Flow:
1. Build a temporary Docker image from `Dockerfile`
2. Mount package recipe into container at `/build/Makefile`
3. Mount host `out/` into container at `/out`
4. Run:

```sh
make -f /build/Makefile all VERSION=<version> ARCH=<arch> OUT_DIR=/out
```

5. Remove container (`--rm`) and temporary image after completion

## Usage examples

Build Tor:

```sh
./build.sh tor tor-0.4.8.18 arm64
```

Build Unbound:

```sh
./build.sh unbound release-1.24.2 arm64
```

Build udp2raw:

```sh
./build.sh udp2raw 20230206.0 arm64
```

Build wghttp:

```sh
./build.sh wghttp v1.0.8 arm64
```

Artifacts are written to:

```text
out/
```

## Output contract

Each recipe should produce:
- `<package>-<arch>.tar.gz`
- `<package>-<arch>.metadata.json`

The metadata file format used in this repository contains:
- package name
- archive filename
- archive sha256
- version
- arch
- per-file sha256 sums

## Recipe contract

Every package recipe Makefile is expected to:

1. Require `VERSION` and `ARCH` variables.
2. Respect `OUT_DIR` (default `/out`).
3. Install only package-specific dependencies (shared build tooling lives in `Dockerfile`).
4. Build static binaries.
5. Package and copy final outputs to `$(OUT_DIR)`.

Common targets pattern:
- `prepare`
- `sys_deps`
- `get_source`
- `dependencies`
- `compile`
- `dist`
- `clean`
- `all` (default build target)

## Static verification

Check binary type from archive without extracting:

```sh
tar -xOf out/<package>-<arch>.tar.gz ./<binary-name> | file -
```

Expected output contains:

```text
statically linked
```

If you copy binary to another Linux host, also check:

```sh
ldd <binary>
```

For a fully static binary, `ldd` should report no dynamic dependencies (often `not a dynamic executable`).

## Notes on current packages

- `tor`: pulls official release tarball from `dist.torproject.org` and links against Alpine static libs.
- `unbound`: pulls source from `https://github.com/NLnetLabs/unbound`, checks out requested ref/tag, and uses `staticexe=-all-static` during make to force static executables.
- `udp2raw`: pulls release source tarball from `https://github.com/wangyu-/udp2raw`, builds with upstream static `all` target, and packages the `udp2raw` binary.
- `wghttp`: pulls source from `https://github.com/brsyuksel/wghttp`, builds with Rust musl target (`x86_64-unknown-linux-musl` or `aarch64-unknown-linux-musl`), and packages the `wghttp` binary.

## Version update automation

Default package versions are stored in `versions.json`.

`update_versions.py` checks upstream tags for stable releases and updates `versions.json` when newer versions exist.

Check only (no file write):

```sh
python3 update_versions.py --check-only
```

Update versions file:

```sh
python3 update_versions.py
```

Exit behavior:

- `0`: no updates found (or successful file update when not check-only)
- `1`: updates are available in check-only mode
- `2`: error (network, parse, or file issue)

## Troubleshooting

### Nightly workflow pushes branch but no PR is created

If `update_versions` pushes `chore/nightly-update-versions` but fails with:

`GitHub Actions is not permitted to create or approve pull requests.`

Use one of these options:

1. Enable **Allow GitHub Actions to create and approve pull requests** in repository settings (Actions → General → Workflow permissions).
2. Add a PAT as repository secret `PR_CREATOR_TOKEN` with permissions to create pull requests in this repo. The workflow will use this token for `create-pull-request`.

### No files in `out/`

Ensure `build.sh` runs `all` target (already implemented) and inspect container logs for recipe failure.

### Configure says tools are missing (e.g. flex/bison)

Those are base build tools and should be added to `Dockerfile`, not to a single package recipe.

### Build succeeds but binary is dynamic

- Confirm recipe passes static flags at configure/build time.
- Confirm static `-dev`/`-static` packages exist in Alpine for all linked libs.
- Verify final artifact with `file` and `ldd` as above.

