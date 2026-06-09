#!/usr/bin/env python3
"""Fix SEO issues identified in site audit."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "seo-config.json"
REPORT_PATH = ROOT / "seo-audit-report.txt"

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL)
DESC_RE = re.compile(r'<meta name="description" content="(.*?)"\s*/>', re.DOTALL)
CANONICAL_RE = re.compile(r'<link rel="canonical" href="([^"]+)"\s*/>')
ROBOTS_RE = re.compile(r'<meta name="robots" content="[^"]*"\s*/>', re.I)
JSONLD_RE = re.compile(
    r'(<script type="application/ld\+json">\s*)(.*?)(\s*</script>)',
    re.DOTALL,
)
H1_BLOG_RE = re.compile(r'<h1 class="newscontent-title">(.*?)</h1>', re.DOTALL)
BLOG_CONTENT_RE = re.compile(
    r'<article class="blogcontent">(?:\s*<p>(.*?)</p>|\s*<h3>(.*?)</h3>)',
    re.DOTALL,
)
OG_TITLE_RE = re.compile(r'<meta property="og:title" content="(.*?)"\s*/>', re.DOTALL)
TWITTER_TITLE_RE = re.compile(r'<meta name="twitter:title" content="(.*?)"\s*/>', re.DOTALL)
OG_DESC_RE = re.compile(r'<meta property="og:description" content="(.*?)"\s*/>', re.DOTALL)
TWITTER_DESC_RE = re.compile(
    r'<meta name="twitter:description" content="(.*?)"\s*/>', re.DOTALL
)

ZERO_OFFERS_RE = re.compile(
    r',?"offers"\s*:\s*\{\s*"@type"\s*:\s*"AggregateOffer"[^}]*"price"\s*:\s*0(?:\.0)?[^}]*\}',
    re.DOTALL,
)
REL_URL_IN_JSON_RE = re.compile(r'"((?:\.\./|\./)[^"]+)"')


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def page_url(rel_path: str, site_url: str) -> str:
    rel = rel_path.replace("\\", "/")
    if rel == "index.html":
        return f"{site_url}/"
    if rel.endswith("/index.html"):
        return f"{site_url}/{rel[:-10]}"
    return f"{site_url}/{rel}"


def resolve_asset_path(asset: str, page_rel: str, site_url: str) -> str:
    if asset.startswith("http://") or asset.startswith("https://"):
        return asset
    page_dir = Path(page_rel).parent.as_posix()
    base = ROOT if page_dir == "." else ROOT / page_dir
    resolved = (base / asset).resolve()
    try:
        rel = resolved.relative_to(ROOT).as_posix()
    except ValueError:
        rel = asset.lstrip("./")
    return f"{site_url}/{rel}"


def fit_title(title: str, max_len: int = 60) -> str:
    title = re.sub(r"\s+", " ", title.strip())
    if len(title) <= max_len:
        return title
    for suffix in (" | KIWL Packaging Blog", " | KIWL", " - KIWL"):
        if suffix in title:
            name = title[: title.rfind(suffix)].strip(" -|")
            room = max_len - len(suffix)
            if room >= 15:
                trimmed = name[:room].rstrip(" -|,&")
                return f"{trimmed}{suffix}"
    return title[: max_len - 1].rstrip(" -|,&") + "…"


def fit_description(desc: str, min_len: int = 50, max_len: int = 160) -> str:
    desc = re.sub(r"\s+", " ", desc.strip())
    if len(desc) > max_len:
        cut = desc[: max_len - 1]
        if " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        desc = cut.rstrip(".,;:") + "…"
    if len(desc) < min_len and not desc.endswith("."):
        desc += "."
    return desc


def is_junk_page(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    return rel in {",.html"} or rel.startswith("uploads/")


def is_noindex_page(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    if is_junk_page(rel):
        return True
    if rel.startswith("showroom/") and rel.endswith("/index.html") and rel != "showroom/index.html":
        return True
    return False


def is_sitemap_page(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    if "_brand_backup" in rel:
        return False
    if is_noindex_page(rel):
        return False
    if rel in {",.html"}:
        return False
    return True


def fix_corrupted_head(text: str) -> tuple[str, bool]:
    if ".<E" not in text and "Explore showroom solutions from KIWL. Wholesale glass bottles, caps and closures for liquor, wine and beverage brands worldwide.<E" not in text:
        return text, False

    desc_m = DESC_RE.search(text)
    title_m = TITLE_RE.search(text)
    if not desc_m or not title_m:
        return text, False

    desc = desc_m.group(1)
    title = title_m.group(1).strip()

    lines = text.split("\n")
    out: list[str] = []
    in_head = False
    fixed = False
    have_twitter_desc = False
    have_og_type = False
    have_og_desc = False

    for line in lines:
        if "<head>" in line:
            in_head = True
        if in_head and line.strip() and not line.strip().startswith("<"):
            fixed = True
            continue
        if in_head:
            if 'name="twitter:description"' in line:
                have_twitter_desc = True
            if 'property="og:type"' in line:
                have_og_type = True
            if 'property="og:description"' in line:
                have_og_desc = True
        out.append(line)
        if in_head and 'name="twitter:title"' in line:
            inserts: list[str] = []
            if not have_twitter_desc:
                inserts.append(
                    f'<meta name="twitter:description" content="{desc}" />'
                )
            if not have_og_type:
                inserts.append('<meta property="og:type" content="website" />')
            if not have_og_desc:
                inserts.append(
                    f'<meta property="og:description" content="{desc}" />'
                )
            if inserts:
                out.extend(inserts)
                fixed = True
        if "</head>" in line:
            in_head = False

    if fixed:
        text = "\n".join(out)
        if not OG_TITLE_RE.search(text):
            text = text.replace(
                f"<title>{title}</title>",
                f"<title>{title}</title>\n<meta property=\"og:title\" content=\"{title}\" />",
                1,
            )
    return text, fixed


def set_robots(text: str, content: str) -> tuple[str, bool]:
    tag = f'<meta name="robots" content="{content}" />'
    if ROBOTS_RE.search(text):
        old = ROBOTS_RE.search(text).group(0)
        if old == tag:
            return text, False
        return ROBOTS_RE.sub(tag, text, count=1), True
    return text.replace("<meta charset", f"{tag}\n<meta charset", 1), True


def extract_blog_description(text: str) -> str | None:
    m = BLOG_CONTENT_RE.search(text)
    if not m:
        return None
    raw = m.group(1) or m.group(2) or ""
    p = re.sub(r"<[^>]+>", "", raw)
    p = re.sub(r"\s+", " ", p).strip()
    if len(p) < 40:
        follow = re.search(
            r'<article class="blogcontent">.*?<p>(.*?)</p>',
            text,
            re.DOTALL,
        )
        if follow:
            p = re.sub(r"<[^>]+>", "", follow.group(1))
            p = re.sub(r"\s+", " ", p).strip()
    if len(p) < 40:
        return None
    return fit_description(p)


def fix_json_ld_block(payload: str, rel: str, site_url: str) -> str:
    payload = ZERO_OFFERS_RE.sub("", payload)

    def abs_url(match: re.Match[str]) -> str:
        path = match.group(1)
        if path.startswith("http"):
            return f'"{path}"'
        return f'"{resolve_asset_path(path, rel, site_url)}"'

    payload = REL_URL_IN_JSON_RE.sub(abs_url, payload)
    return payload


def restore_empty_product_pages() -> list[str]:
    """Rebuild known empty product pages from a sibling template."""
    restored: list[str] = []
    target = ROOT / "bottle-cap/oil-cap/olive-oil-aluminum-plastic-caps-with-ropp.html"
    template = ROOT / "bottle-cap/oil-cap/olive-oil-aluminum-cap-with-plastic-insert.html"
    if not target.exists() or target.stat().st_size > 100:
        return restored
    if not template.exists():
        return restored

    src_name = "olive-oil-aluminum-cap-with-plastic-insert"
    dst_name = "olive-oil-aluminum-plastic-caps-with-ropp"
    title_old = "Olive Oil Aluminum Cap With Plastic Insert"
    title_new = "Olive Oil Aluminum Plastic Caps With ROPP"

    text = template.read_text(encoding="utf-8")
    text = text.replace(src_name, dst_name)
    text = text.replace(title_old, title_new)
    text = text.replace("Wholesal - KIWL", "Wholesale - KIWL")
    text = text.replace(
        "Olive Oil Aluminum Plastic Caps With ROPP | Wholesale Manufacturer - KIWL",
        "Olive Oil Aluminum Plastic Caps With ROPP | Wholesale - KIWL",
    )
    target.write_text(text, encoding="utf-8")
    restored.append(target.relative_to(ROOT).as_posix())
    return restored


def add_junk_page_stubs() -> list[str]:
    """Ensure junk/utility HTML paths emit noindex and canonical."""
    changed: list[str] = []
    cfg = load_config()
    site_url = cfg["site_url"]
    junk_paths = [
        ",.html",
        "uploads/202211134-aluminum-cap-screw-bottle-roppcap40186768264.html",
        "uploads/11134/products/20250226143755d4273beb3.html",
        "uploads/11134/products/202508201525239bd18beb3.html",
    ]
    stub = (
        '<!doctype html><html lang="en"><head>'
        '<meta charset="utf-8" />'
        '<meta name="robots" content="noindex, nofollow" />'
        '<title>404 Page not found - KIWL</title>'
        '<link rel="canonical" href="{url}" />'
        '</head><body><p>Page not found.</p></body></html>'
    )
    for rel in junk_paths:
        path = ROOT / rel
        if not path.exists():
            continue
        url = page_url(rel, site_url)
        content = stub.format(url=url)
        if path.read_text(encoding="utf-8", errors="ignore") != content:
            path.write_text(content, encoding="utf-8")
            changed.append(rel)
    return changed


def cfg_same_as() -> list[str]:
    cfg = load_config()
    return cfg.get(
        "same_as",
        ["https://www.youtube.com/watch?v=jJIceDZ-JtM"],
    )


def sync_meta_tags(text: str, title: str, desc: str) -> str:
    if TITLE_RE.search(text):
        text = TITLE_RE.sub(f"<title>{title}</title>", text, count=1)
    if DESC_RE.search(text):
        text = DESC_RE.sub(f'<meta name="description" content="{desc}" />', text, count=1)
    for tag_re in (OG_TITLE_RE, TWITTER_TITLE_RE):
        if tag_re.search(text):
            text = tag_re.sub(
                lambda m, t=title: m.group(0).replace(m.group(1), t.replace('"', "&quot;")),
                text,
                count=1,
            )
    for tag_re in (OG_DESC_RE, TWITTER_DESC_RE):
        if tag_re.search(text):
            text = tag_re.sub(
                lambda m, d=desc: m.group(0).replace(m.group(1), d.replace('"', "&quot;")),
                text,
                count=1,
            )
    return text


def ensure_canonical(text: str, rel: str, site_url: str) -> tuple[str, bool]:
    url = page_url(rel, site_url)
    if CANONICAL_RE.search(text):
        old = CANONICAL_RE.search(text).group(1)
        if old == url:
            return text, False
        return CANONICAL_RE.sub(f'<link rel="canonical" href="{url}" />', text, count=1), True
    return text.replace("</head>", f'<link rel="canonical" href="{url}" />\n</head>', 1), True


def generate_sitemap(site_url: str, html_files: list[Path]) -> str:
    urls: list[str] = []
    for hf in html_files:
        rel = hf.relative_to(ROOT).as_posix()
        if not is_sitemap_page(rel):
            continue
        urls.append(page_url(rel, site_url))
    urls = sorted(set(urls))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        parts.append("  <url>")
        parts.append(f"    <loc>{url}</loc>")
        parts.append(f"    <lastmod>{today}</lastmod>")
        parts.append("    <changefreq>weekly</changefreq>")
        parts.append("    <priority>0.8</priority>")
        parts.append("  </url>")
    parts.append("</urlset>")
    return "\n".join(parts) + "\n"


def fix_page(text: str, rel: str, cfg: dict) -> tuple[str, list[str]]:
    changes: list[str] = []
    site_url = cfg["site_url"]
    rel_posix = rel.replace("\\", "/")

    text, corrupted = fix_corrupted_head(text)
    if corrupted:
        changes.append("corrupted-meta")

    text, canon_changed = ensure_canonical(text, rel_posix, site_url)
    if canon_changed:
        changes.append("canonical")

    if is_noindex_page(rel_posix):
        text, robots_changed = set_robots(text, "noindex, follow")
        if robots_changed:
            changes.append("noindex")

    title_m = TITLE_RE.search(text)
    desc_m = DESC_RE.search(text)
    title = title_m.group(1).strip() if title_m else ""
    desc = desc_m.group(1).strip() if desc_m else ""

    if rel_posix.startswith("blog/") and rel_posix.endswith(".html") and "/page/" not in rel_posix:
        blog_desc = extract_blog_description(text)
        if blog_desc and (
            "Learn from KIWL" in desc
            or desc.strip().endswith("?")
            or len(desc) < 80
        ):
            desc = blog_desc
            changes.append("blog-desc-from-content")
        elif "Learn from KIWL" in desc:
            question = title.replace(" | KIWL Packaging Blog", "").strip()
            desc = fit_description(
                f"{question}. Packaging tips and wholesale solutions from KIWL, "
                "China spirits and beverage packaging manufacturer."
            )
            changes.append("blog-desc-from-title")

    old_title, old_desc = title, desc
    new_title = fit_title(title)
    new_desc = fit_description(desc)
    blog_desc_changed = "blog-desc-from-content" in changes or "blog-desc-from-title" in changes
    if new_title != old_title or new_desc != old_desc or blog_desc_changed:
        text = sync_meta_tags(text, new_title, new_desc)
        title, desc = new_title, new_desc
        if new_title != old_title or new_desc != old_desc:
            changes.append("title-desc-trim")
    m = JSONLD_RE.search(text)
    if m:
        fixed_payload = fix_json_ld_block(m.group(2), rel_posix, site_url)
        if blog_desc_changed and desc:
            fixed_payload = re.sub(
                r'("description"\s*:\s*")(?:[^"\\]|\\.)*(")',
                lambda match, d=desc: f'{match.group(1)}{d.replace(chr(34), "")}{match.group(2)}',
                fixed_payload,
            )
        if fixed_payload != m.group(2):
            text = text[: m.start()] + m.group(1) + fixed_payload + m.group(3) + text[m.end() :]
            changes.append("json-ld-fix")

    if (
        rel_posix.startswith("blog/")
        and desc
        and "Learn from KIWL" not in desc
    ):
        m = JSONLD_RE.search(text)
        if m and "Learn from KIWL" in m.group(2):
            payload = re.sub(
                r'("description"\s*:\s*")(?:[^"\\]|\\.)*(")',
                lambda match, d=desc: f'{match.group(1)}{d.replace(chr(34), "")}{match.group(2)}',
                m.group(2),
            )
            if payload != m.group(2):
                text = text[: m.start()] + m.group(1) + payload + m.group(3) + text[m.end() :]
                changes.append("blog-json-ld-sync")

    if rel_posix == "index.html":
        m = JSONLD_RE.search(text)
        if m and '"sameAs":[]' in m.group(2):
            same_as = json.dumps(cfg_same_as())
            payload = m.group(2).replace('"sameAs":[]', f'"sameAs":{same_as}')
            text = text[: m.start()] + m.group(1) + payload + m.group(3) + text[m.end() :]
            changes.append("sameAs")

    return text, changes


def audit(cfg: dict, html_files: list[Path]) -> dict:
    stats = {
        "pages": len(html_files),
        "missing_canonical": 0,
        "long_title": 0,
        "long_desc": 0,
        "short_desc": 0,
        "noindex_pages": 0,
        "zero_price_jsonld": 0,
        "corrupted_meta": 0,
        "relative_jsonld": 0,
    }
    for hf in html_files:
        rel = hf.relative_to(ROOT).as_posix()
        text = hf.read_text(encoding="utf-8", errors="ignore")
        if not CANONICAL_RE.search(text):
            stats["missing_canonical"] += 1
        tm = TITLE_RE.search(text)
        if tm and len(tm.group(1)) > 60:
            stats["long_title"] += 1
        dm = DESC_RE.search(text)
        if dm:
            if len(dm.group(1)) > 160:
                stats["long_desc"] += 1
            if len(dm.group(1)) < 50:
                stats["short_desc"] += 1
        if ROBOTS_RE.search(text) and "noindex" in ROBOTS_RE.search(text).group(0).lower():
            stats["noindex_pages"] += 1
        if ".<E" in text:
            stats["corrupted_meta"] += 1
        if '"price":0.0' in text or '"lowPrice":0.0' in text:
            stats["zero_price_jsonld"] += 1
        if re.search(r'"\.\./[^"]+"', text):
            stats["relative_jsonld"] += 1
    sm = ROOT / "sitemap.xml"
    if sm.exists():
        stats["sitemap_urls"] = len(re.findall(r"<loc>", sm.read_text(encoding="utf-8")))
    return stats


def main() -> None:
    cfg = load_config()
    html_files = sorted(
        p for p in ROOT.rglob("*.html") if "_brand_backup" not in str(p)
    )

    restored = restore_empty_product_pages()
    junk_fixed = add_junk_page_stubs()

    before = audit(cfg, html_files)
    stats: dict[str, int] = {}
    changed = 0

    for hf in html_files:
        rel = hf.relative_to(ROOT).as_posix()
        original = hf.read_text(encoding="utf-8", errors="ignore")
        updated, changes = fix_page(original, rel, cfg)
        if updated != original:
            hf.write_text(updated, encoding="utf-8")
            changed += 1
            for c in changes:
                stats[c] = stats.get(c, 0) + 1

    sitemap_text = generate_sitemap(cfg["site_url"], html_files)
    (ROOT / "sitemap.xml").write_text(sitemap_text, encoding="utf-8")
    stats["sitemap-regenerated"] = 1

    robots = ROOT / "robots.txt"
    robots.write_text(
        "User-agent: *\nAllow: /\n\nSitemap: "
        f"{cfg['site_url']}/sitemap.xml\n",
        encoding="utf-8",
    )

    after = audit(cfg, html_files)

    report = [
        f"SEO FIX REPORT - {cfg['site_url']}",
        "=" * 50,
        "",
        f"Restored product pages: {restored}",
        f"Junk page stubs: {junk_fixed}",
        "",
        "--- BEFORE ---",
        *[f"{k}: {v}" for k, v in before.items()],
        "",
        "--- AFTER ---",
        *[f"{k}: {v}" for k, v in after.items()],
        "",
        "--- CHANGES ---",
        f"HTML files modified: {changed}/{len(html_files)}",
        json.dumps(stats, indent=2),
        "",
        "--- FIXES APPLIED ---",
        "1. Repaired corrupted meta tags (showroom/index.html)",
        "2. noindex,follow on showroom tag pages and uploads/*.html",
        "3. Removed zero-price offers from JSON-LD",
        "4. Absolute URLs in JSON-LD relative paths",
        "5. Title trimmed to <=60 chars, description to <=160 chars",
        "6. Blog meta descriptions from first paragraph where possible",
        "7. Organization sameAs on homepage",
        "8. Full sitemap regeneration (excluding noindex pages)",
        "9. Missing canonical tags added",
    ]
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")

    print("=== BEFORE ===")
    print(before)
    print("\n=== AFTER ===")
    print(after)
    print(f"\nModified: {changed}/{len(html_files)}")
    print("Stats:", stats)


if __name__ == "__main__":
    main()
