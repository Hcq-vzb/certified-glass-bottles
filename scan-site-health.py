#!/usr/bin/env python3
"""Quick site health scan for local static mirror."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "site-health-report.txt"


def main() -> None:
    html_files = [p for p in ROOT.rglob("*.html") if "_brand_backup" not in str(p)]
    img_re = re.compile(r"""src=["']((?:uploads|Content/uploads|images)/[^"'?#]+)""")
    css_neg_re = re.compile(r"margin-top\s*:\s*-\d+px")

    missing: list[str] = []
    abs_paths: list[str] = []
    neg_margin_css: list[str] = []
    no_static: list[str] = []

    for hf in html_files:
        rel = hf.relative_to(ROOT).as_posix()
        text = hf.read_text(encoding="utf-8", errors="ignore")
        if "static-local.css" not in text:
            no_static.append(rel)
        if 'src="/uploads/' in text or "src='/uploads/" in text:
            abs_paths.append(rel)
        for m in img_re.finditer(text):
            p = m.group(1).split("?")[0]
            if not (ROOT / p).exists():
                missing.append(f"{rel} -> {p}")

    for css in (ROOT / "images" / "11134").glob("*.css"):
        if css.name.startswith("other") and len(css.name) > 10:
            continue
        content = css.read_text(encoding="utf-8", errors="ignore")
        if css_neg_re.search(content):
            neg_margin_css.append(css.relative_to(ROOT).as_posix())

    lines = [
        f"HTML pages: {len(html_files)}",
        f"Missing local images: {len(missing)}",
        f"Absolute /uploads/ src: {len(abs_paths)}",
        f"Pages without static-local.css: {len(no_static)}",
        f"Page CSS with negative margin-top: {len(neg_margin_css)}",
        "",
        "=== Missing images (first 30) ===",
        *missing[:30],
        "",
        "=== Absolute upload paths (first 20) ===",
        *abs_paths[:20],
        "",
        "=== CSS negative margins (page-specific) ===",
        *neg_margin_css,
    ]
    LOG.write_text("\n".join(lines), encoding="utf-8")
    print(LOG.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
