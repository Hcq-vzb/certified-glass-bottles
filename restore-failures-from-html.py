#!/usr/bin/env python3
"""Resolve failed restore paths by scraping live page HTML for real image URLs."""

from __future__ import annotations

import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / "restore-from-origin-log.txt"
FAIL_LOG = ROOT / "restore-failures-log.txt"
SITE = "https://www.spiritsglass.com/"
UA = {"User-Agent": "Mozilla/5.0"}


def log(msg: str) -> None:
    print(msg)
    with FAIL_LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def failed_paths() -> list[str]:
    if not LOG_FILE.exists():
        return []
    fails: list[str] = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("[fail] "):
            fails.append(line[7:].strip())
        elif line.startswith("[fail-http] "):
            part = line[12:].split(" -> ", 1)[0].strip()
            fails.append(part)
    return list(dict.fromkeys(fails))


def local_html_for_image(rel_img: str) -> list[Path]:
    rel = rel_img.replace("\\", "/")
    name = Path(rel).name
    hits: list[Path] = []
    for html in ROOT.rglob("*.html"):
        try:
            text = html.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if rel in text or name in text:
            hits.append(html)
    return hits[:3]


def live_page_url(local_html: Path) -> str:
    rel = local_html.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return SITE
    return SITE + rel


def extract_upload_urls(html: str) -> list[str]:
    return list(
        dict.fromkeys(
            re.findall(
                r"(?:https?://(?:www\.)?spiritsglass\.com)?/?((?:uploads|Content/uploads)/[^\"'\s?#]+\.(?:jpg|jpeg|png|gif|webp))",
                html,
                flags=re.I,
            )
        )
    )


def download_url_to_path(url_path: str, dest: Path) -> bool:
    url = SITE + url_path.lstrip("/")
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=90
        ) as resp:
            data = resp.read()
    except Exception as exc:
        log(f"[fail-dl] {dest.relative_to(ROOT)} <- {url} ({exc})")
        return False
    if len(data) < 500:
        log(f"[fail-small] {dest.relative_to(ROOT)} <- {url}")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    log(f"[ok] {dest.relative_to(ROOT)} ({len(data)} bytes) <- {url}")
    return True


def pick_best_url(urls: list[str], local_name: str) -> str | None:
    if not urls:
        return None
    stem = Path(local_name).stem.lower()
    for u in urls:
        if Path(u).name.lower() == local_name.lower():
            return u
    for u in urls:
        if stem[:12] in Path(u).name.lower():
            return u
    if len(urls) == 1:
        return urls[0]
    return urls[0]


def main() -> int:
    if FAIL_LOG.exists():
        FAIL_LOG.unlink()
    fails = failed_paths()
    log(f"Retrying {len(fails)} failed paths via live HTML")
    ok = miss = 0
    cache: dict[str, str] = {}

    for rel in fails:
        dest = ROOT / rel.replace("/", "\\")
        htmls = local_html_for_image(rel)
        if not htmls:
            log(f"[no-html] {rel}")
            miss += 1
            continue

        chosen = None
        for html in htmls:
            page = live_page_url(html)
            if page not in cache:
                try:
                    raw = urllib.request.urlopen(
                        urllib.request.Request(page, headers=UA), timeout=60
                    ).read().decode("utf-8", "ignore")
                except Exception as exc:
                    log(f"[fail-page] {page} ({exc})")
                    cache[page] = ""
                    continue
                cache[page] = raw
            raw = cache[page]
            if not raw:
                continue
            urls = extract_upload_urls(raw)
            chosen = pick_best_url(urls, Path(rel).name)
            if chosen:
                break

        if not chosen:
            log(f"[no-url] {rel}")
            miss += 1
            continue

        if download_url_to_path(chosen, dest):
            ok += 1
        else:
            miss += 1
        time.sleep(0.2)

    log(f"Done: ok={ok}, miss={miss}")
    return 0 if miss == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
