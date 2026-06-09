#!/usr/bin/env python3
"""Post-fix SEO validation for Google Rich Results readiness."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "seo-config.json"
REPORT_PATH = ROOT / "seo-verify-report.txt"

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL)
DESC_RE = re.compile(r'<meta name="description" content="(.*?)"\s*/>', re.DOTALL)
CANONICAL_RE = re.compile(r'<link rel="canonical" href="([^"]+)"\s*/>')
OG_URL_RE = re.compile(r'<meta property="og:url" content="([^"]+)"\s*/>')
JSONLD_RE = re.compile(
    r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
    re.DOTALL,
)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL)

SAMPLE_PAGES = [
    "index.html",
    "factory.html",
    "faq.html",
    "products.html",
    "bottle-cap/index.html",
    "bottle-cap/t-shape-wooden-bottle-cap.html",
    "blog/index.html",
    "blog/can-screw-caps-keep-wine-fresh-for-a-long-time-2580218.html",
    "liquor-bottles/spirits-bottles/750ml-gin-vodka-liquor-glass-bottle.html",
    "newslist-1.html",
]


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def page_url(rel_path: str, site_url: str) -> str:
    rel = rel_path.replace("\\", "/")
    if rel == "index.html":
        return f"{site_url}/"
    if rel.endswith("/index.html"):
        return f"{site_url}/{rel[:-10]}"
    return f"{site_url}/{rel}"


def check_page(rel: str, site_url: str) -> list[str]:
    path = ROOT / rel
    if not path.exists():
        return [f"{rel}: MISSING"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    issues: list[str] = []
    canonical = CANONICAL_RE.search(text)
    og_url = OG_URL_RE.search(text)
    desc = DESC_RE.search(text)
    expected = page_url(rel, site_url)

    if not canonical:
        issues.append("missing canonical")
    elif canonical.group(1) != expected:
        issues.append(f"canonical mismatch: {canonical.group(1)} != {expected}")

    if og_url and canonical and og_url.group(1) != canonical.group(1):
        issues.append("og:url != canonical")

    if desc and len(desc.group(1)) < 50:
        issues.append(f"short description ({len(desc.group(1))} chars)")

    m = JSONLD_RE.search(text)
    if m:
        payload = m.group(1)
        if re.search(r'"\.\./[^"]+"', payload):
            issues.append("relative URL in JSON-LD")
        if rel.endswith(".html") and rel != "index.html" and not rel.endswith("/index.html"):
            wrong = f"{site_url}/{rel[:-5]}"
            if re.search(re.escape(wrong) + r'(?!\.html)', payload):
                issues.append("JSON-LD url without .html extension")

    if rel == "faq.html" and '"FAQPage"' not in text:
        issues.append("missing FAQPage schema")

    h1s = H1_RE.findall(text)
    if len(h1s) > 1 and "prodetails-name" in text:
        issues.append(f"multiple H1 tags ({len(h1s)})")

    return issues


def main() -> None:
    cfg = load_config()
    site_url = cfg["site_url"]
    html_files = sorted(
        p for p in ROOT.rglob("*.html") if "_brand_backup" not in str(p)
    )

    short_desc = 0
    jsonld_mismatch = 0
    missing_faq = 0
    sample_results: list[str] = []

    for hf in html_files:
        rel = hf.relative_to(ROOT).as_posix()
        text = hf.read_text(encoding="utf-8", errors="ignore")
        dm = DESC_RE.search(text)
        if dm and len(dm.group(1)) < 50:
            short_desc += 1
        m = JSONLD_RE.search(text)
        if m:
            payload = m.group(1)
            if (
                rel.endswith(".html")
                and rel != "index.html"
                and not rel.endswith("/index.html")
            ):
                wrong = f"{site_url}/{rel[:-5]}"
                if re.search(re.escape(wrong) + r"(?!\.html)", payload):
                    jsonld_mismatch += 1
        if rel == "faq.html" and '"FAQPage"' not in text:
            missing_faq += 1

    for rel in SAMPLE_PAGES:
        issues = check_page(rel, site_url)
        status = "PASS" if not issues else "FAIL"
        sample_results.append(f"  [{status}] {rel}")
        for issue in issues:
            sample_results.append(f"         - {issue}")

    rich_results_urls = [
        f"{site_url}/",
        f"{site_url}/factory.html",
        f"{site_url}/faq.html",
        f"{site_url}/bottle-cap/t-shape-wooden-bottle-cap.html",
        f"{site_url}/blog/can-screw-caps-keep-wine-fresh-for-a-long-time-2580218.html",
    ]

    report = [
        f"SEO VERIFICATION REPORT - {site_url}",
        "=" * 50,
        "",
        "--- SITE-WIDE COUNTS ---",
        f"Total pages: {len(html_files)}",
        f"Short descriptions (<50 chars): {short_desc}",
        f"JSON-LD URL mismatches: {jsonld_mismatch}",
        f"Missing FAQPage schema: {missing_faq}",
        "",
        "--- SAMPLE PAGE CHECKS ---",
        *sample_results,
        "",
        "--- MANUAL RICH RESULTS TEST (paste in browser) ---",
        "https://search.google.com/test/rich-results",
        "",
        *rich_results_urls,
        "",
        "--- SEARCH CONSOLE ---",
        "https://search.google.com/search-console",
        "Check: Coverage, Core Web Vitals, Enhancements (Product, FAQ, Breadcrumb)",
        "",
        "--- PAGESPEED INSIGHTS ---",
        "https://pagespeed.web.dev/",
        f"Test: {site_url}/",
    ]
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"\nReport saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
