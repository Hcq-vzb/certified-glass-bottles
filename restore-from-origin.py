#!/usr/bin/env python3
"""Re-download modified images from www.spiritsglass.com with resume + fallbacks."""

from __future__ import annotations

import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIST_FILE = ROOT / "restore-modified-images-list.txt"
LOG_FILE = ROOT / "restore-from-origin-log.txt"
BASE_URL = "https://www.spiritsglass.com/"
UA = {"User-Agent": "Mozilla/5.0"}


def log(msg: str) -> None:
    print(msg)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def already_ok(rel_path: str) -> bool:
    if not LOG_FILE.exists():
        return False
    needle = f"[ok] {rel_path.replace(chr(92), '/')}"
    return needle in LOG_FILE.read_text(encoding="utf-8")


def candidate_urls(rel_path: str) -> list[str]:
    rel = rel_path.replace("\\", "/").lstrip("/")
    urls = [BASE_URL + rel]
    name = Path(rel).name
    parent = str(Path(rel).parent).replace("\\", "/")
    if not name.startswith("p") and parent.startswith("uploads/"):
        urls.append(f"{BASE_URL}{parent}/p{name}")
    if name == "favicon.jpg":
        urls.append(BASE_URL + "uploads/11134/favicon.ico")
    return urls


def try_download(url: str, timeout: int = 90) -> bytes | None:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except Exception:
        return None
    if len(data) < 200:
        return None
    if url.endswith("favicon.ico") and len(data) < 500:
        return None
    return data


def download(rel_path: str) -> bool:
    dest = ROOT / rel_path.replace("/", "\\")
    for url in candidate_urls(rel_path):
        data = try_download(url)
        if data is None:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        log(f"[ok] {rel_path.replace(chr(92), '/')} ({len(data)} bytes) <- {url}")
        return True
    log(f"[fail] {rel_path.replace(chr(92), '/')}")
    return False


def main() -> int:
    paths = [
        line.strip()
        for line in LIST_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if not LOG_FILE.exists():
        log(f"Restoring {len(paths)} files from {BASE_URL}")

    ok = fail = skip = 0
    for i, rel in enumerate(paths, 1):
        rel_norm = rel.replace("\\", "/")
        if already_ok(rel_norm):
            skip += 1
            continue
        if download(rel_norm):
            ok += 1
        else:
            fail += 1
        if i % 10 == 0:
            time.sleep(0.3)

    log(f"Done: ok={ok}, fail={fail}, skip={skip}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
