#!/usr/bin/env python3
"""Restore modified images using original URLs from HTTrack cache."""

from __future__ import annotations

import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTS_CACHE = ROOT.parent / "hts-cache" / "new.txt"
LIST_FILE = ROOT / "restore-modified-images-list.txt"
LOG_FILE = ROOT / "restore-hts-cache-log.txt"
UA = {"User-Agent": "Mozilla/5.0"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def log(msg: str) -> None:
    print(msg)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def norm_local(path: str) -> str:
    p = path.replace("\\", "/")
    if "www.spiritsglass.com/" in p:
        p = p.split("www.spiritsglass.com/", 1)[1]
    return p.lstrip("/")


def load_url_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not HTS_CACHE.exists():
        return mapping
    for line in HTS_CACHE.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "https://" not in line:
            continue
        parts = line.split("\t")
        if len(parts) < 9:
            continue
        url = parts[7]
        local = urllib.parse.unquote(parts[8].split(" ", 1)[0])
        if not url.startswith("https://"):
            continue
        if Path(norm_local(local)).suffix.lower() not in IMAGE_EXT:
            continue
        mapping[norm_local(local)] = url
    return mapping


def download(url: str, dest: Path) -> bool:
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=90
        ) as resp:
            data = resp.read()
    except Exception as exc:
        log(f"[fail] {dest.relative_to(ROOT)} <- {url} ({exc})")
        return False
    if len(data) < 300:
        log(f"[fail-small] {dest.relative_to(ROOT)} <- {url}")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    log(f"[ok] {dest.relative_to(ROOT)} ({len(data)} bytes) <- {url}")
    return True


def main() -> int:
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    targets = [
        line.strip()
        for line in LIST_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    url_map = load_url_map()
    log(f"HTS cache mappings: {len(url_map)}, targets: {len(targets)}")

    ok = miss = 0
    for rel in targets:
        rel_norm = rel.replace("\\", "/")
        dest = ROOT / rel_norm.replace("/", "\\")
        url = url_map.get(rel_norm)
        if not url:
            log(f"[no-map] {rel_norm}")
            miss += 1
            continue
        if download(url, dest):
            ok += 1
        else:
            miss += 1
        time.sleep(0.15)

    log(f"Done: ok={ok}, miss={miss}")
    return 0 if miss == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
