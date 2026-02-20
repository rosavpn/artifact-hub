#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

VERSIONS_FILE = Path(__file__).resolve().parent / "versions.json"

SKIP_KEYWORDS = (
    "alpha",
    "beta",
    "rc",
    "test",
    "pre",
    "preview",
    "dev",
    "snapshot",
)


def fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "artifact-hub-version-checker/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read()
    return json.loads(data.decode("utf-8"))


def is_stable_tag(tag: str) -> bool:
    lowered = tag.lower()
    return not any(keyword in lowered for keyword in SKIP_KEYWORDS)


def normalize_tor_tag(tag: str) -> Optional[str]:
    if not tag.startswith("tor-"):
        return None
    if re.fullmatch(r"tor-\d+(?:\.\d+)+", tag) is None:
        return None
    return tag


def normalize_unbound_tag(tag: str) -> Optional[str]:
    if not tag.startswith("release-"):
        return None
    if re.fullmatch(r"release-\d+(?:\.\d+)+", tag) is None:
        return None
    return tag


def normalize_udp2raw_tag(tag: str) -> Optional[str]:
    if re.fullmatch(r"\d+(?:\.\d+)+", tag) is None:
        return None
    return tag


def normalize_wghttp_tag(tag: str) -> Optional[str]:
    if re.fullmatch(r"v\d+(?:\.\d+)+", tag) is None:
        return None
    return tag


def version_key(tag: str) -> Tuple[int, ...]:
    numbers = [int(part) for part in re.findall(r"\d+", tag)]
    return tuple(numbers)


def pick_latest(tags: Iterable[str], normalizer: Callable[[str], Optional[str]]) -> Optional[str]:
    candidates: List[str] = []
    for tag in tags:
        if not is_stable_tag(tag):
            continue
        normalized = normalizer(tag)
        if normalized is None:
            continue
        candidates.append(normalized)

    if not candidates:
        return None

    return max(candidates, key=version_key)


def fetch_tor_tags(max_pages: int = 6) -> List[str]:
    tags: List[str] = []
    base = "https://gitlab.torproject.org/api/v4/projects/tpo%2Fcore%2Ftor/repository/tags"
    for page in range(1, max_pages + 1):
        url = f"{base}?per_page=100&page={page}"
        data = fetch_json(url)
        if not isinstance(data, list) or not data:
            break
        for item in data:
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str):
                    tags.append(name)
    return tags


def fetch_github_tags(owner: str, repo: str, max_pages: int = 6) -> List[str]:
    tags: List[str] = []
    base = f"https://api.github.com/repos/{owner}/{repo}/tags"
    for page in range(1, max_pages + 1):
        url = f"{base}?per_page=100&page={page}"
        data = fetch_json(url)
        if not isinstance(data, list) or not data:
            break
        for item in data:
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str):
                    tags.append(name)
    return tags


def read_versions(path: Path) -> Dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("versions.json must contain an object")

    result: Dict[str, str] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, str):
            result[key] = value
    return result


def write_versions(path: Path, versions: Dict[str, str]) -> None:
    path.write_text(json.dumps(versions, indent=4, sort_keys=False) + "\n", encoding="utf-8")


def resolve_latest_versions() -> Dict[str, str]:
    latest: Dict[str, str] = {}

    tor_latest = pick_latest(fetch_tor_tags(), normalize_tor_tag)
    if tor_latest is None:
        raise RuntimeError("Could not determine latest stable tor version")
    latest["tor"] = tor_latest

    unbound_latest = pick_latest(fetch_github_tags("NLnetLabs", "unbound"), normalize_unbound_tag)
    if unbound_latest is None:
        raise RuntimeError("Could not determine latest stable unbound version")
    latest["unbound"] = unbound_latest

    udp2raw_latest = pick_latest(fetch_github_tags("wangyu-", "udp2raw"), normalize_udp2raw_tag)
    if udp2raw_latest is None:
        raise RuntimeError("Could not determine latest stable udp2raw version")
    latest["udp2raw"] = udp2raw_latest

    wghttp_latest = pick_latest(fetch_github_tags("brsyuksel", "wghttp"), normalize_wghttp_tag)
    if wghttp_latest is None:
        raise RuntimeError("Could not determine latest stable wghttp version")
    latest["wghttp"] = wghttp_latest

    return latest


def check_updates(current: Dict[str, str], latest: Dict[str, str]) -> List[Tuple[str, str, str]]:
    updates: List[Tuple[str, str, str]] = []
    for package in ("tor", "unbound", "udp2raw", "wghttp"):
        cur = current.get(package)
        lat = latest.get(package)
        if cur is None or lat is None:
            continue
        if cur != lat:
            updates.append((package, cur, lat))
    return updates


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check latest stable versions for artifact-hub packages")
    parser.add_argument("--check-only", action="store_true", help="Only check for updates, do not write versions.json")
    parser.add_argument("--file", type=Path, default=VERSIONS_FILE, help="Path to versions.json")
    args = parser.parse_args(argv)

    try:
        current = read_versions(args.file)
        latest = resolve_latest_versions()
    except (OSError, ValueError, RuntimeError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    updates = check_updates(current, latest)

    if not updates:
        print("versions.json is up to date (stable versions only).")
        return 0

    print("Updates available:")
    for package, cur, lat in updates:
        print(f"- {package}: {cur} -> {lat}")

    if args.check_only:
        return 1

    merged = dict(current)
    for package, _, lat in updates:
        merged[package] = lat
    write_versions(args.file, merged)
    print(f"Updated {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
