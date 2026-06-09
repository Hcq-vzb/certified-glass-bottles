#!/usr/bin/env python3
"""Bulk SEO optimization for www.certifiedglassbottles.com static site."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "seo-config.json"
REPORT_PATH = ROOT / "seo-audit-report.txt"

HTTRACK_START = re.compile(
    r"\n<!-- Mirrored from www\.(?:certifiedglassbottles|spiritsglass)\.com.*?-->\n"
    r"<!-- Added by HTTrack -->.*?<!-- /Added by HTTrack -->",
    re.DOTALL,
)
HTTRACK_END = re.compile(
    r"\n<!-- Mirrored from www\.(?:certifiedglassbottles|spiritsglass)\.com.*?-->\s*$",
    re.DOTALL,
)
JSONLD_RE = re.compile(
    r'(<script type="application/ld\+json">\s*)(.*?)(\s*</script>)',
    re.DOTALL,
)

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL)
DESC_RE = re.compile(r'<meta name="description" content="(.*?)"\s*/>', re.DOTALL)
KEYWORDS_RE = re.compile(r'<meta name="keywords" content="(.*?)"\s*/>', re.DOTALL)
H1_PRODUCT_RE = re.compile(r'<h1 class="prodetails-name">(.*?)</h1>', re.DOTALL)
H1_BLOG_RE = re.compile(r'<h1 class="newscontent-title">(.*?)</h1>', re.DOTALL)
CANONICAL_RE = re.compile(r'<link rel="canonical" href="([^"]+)"\s*/>')
HREFLANG_RE = re.compile(
    r'(<link rel="alternate" hreflang="[^"]+" href=")([^"]+)("\s*/>)'
)
OG_URL_RE = re.compile(r'<meta property="og:url" content="([^"]+)"\s*/>')
OG_IMAGE_RE = re.compile(r'<meta property="og:image" content="([^"]+)"\s*/>')
TWITTER_IMAGE_RE = re.compile(r'<meta name="twitter:image" content="([^"]+)"\s*/>')
TWITTER_TITLE_RE = re.compile(r'<meta name="twitter:title" content="(.*?)"\s*/>', re.DOTALL)
TWITTER_DESC_RE = re.compile(
    r'<meta name="twitter:description" content="(.*?)"\s*/>', re.DOTALL
)
OG_TITLE_RE = re.compile(r'<meta property="og:title" content="(.*?)"\s*/>', re.DOTALL)
OG_DESC_RE = re.compile(r'<meta property="og:description" content="(.*?)"\s*/>', re.DOTALL)
TWITTER_CARD_RE = re.compile(r'<meta name="twitter:card" content="summary"\s*/>')

OLD_TITLE_PATTERNS = [
    re.compile(
        r"^China (.+?) Manufacturers Suppliers Factory(?: - Wholesale (?:Service )?)?(?: - )?(?:KIWL|LIQUORPAC)(?: - Page \d+)?$",
        re.I,
    ),
    re.compile(
        r"^China (.+?) Manufacturers Suppliers Factory - KIWL(?: - Page \d+)?$",
        re.I,
    ),
    re.compile(
        r"^China (.+?) Manufacturers Suppliers Factory - Wholesale Service - KIWL(?: - Page \d+)?$",
        re.I,
    ),
    re.compile(
        r"^China (.+?) Manufacturers Suppliers Factory - Wholesale (.+?) - (?:KIWL|LIQUORPAC)(?: - Page \d+)?$",
        re.I,
    ),
    re.compile(
        r"^News - China (.+?) Manufacturers Suppliers Factory - KIWL(?: - Page \d+)?$",
        re.I,
    ),
    re.compile(
        r"^(.+?) - China \1 Manufacturers Suppliers Factory - KIWL$",
        re.I,
    ),
]


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def site_host(cfg: dict) -> str:
    return cfg["site_url"].replace("https://", "").replace("http://", "").rstrip("/")


def replace_foreign_domains(text: str, cfg: dict) -> str:
    host = site_host(cfg)
    for alt in {cfg.get("old_domain", ""), "www.spiritsglass.com", "www.certifiedglassbottles.com"}:
        if not alt or alt == host:
            continue
        text = text.replace(f"https://{alt}", cfg["site_url"])
        text = text.replace(f"http://{alt}", cfg["site_url"])
        text = text.replace(alt, host)
    return text


def slug_to_title(slug: str) -> str:
    return " ".join(word.capitalize() for word in slug.replace("-", " ").split())


def page_url(rel_path: str, site_url: str) -> str:
    rel = rel_path.replace("\\", "/")
    if rel == "index.html":
        return f"{site_url}/"
    if rel.endswith("/index.html"):
        return f"{site_url}/{rel[:-10]}"
    return f"{site_url}/{rel}"


def resolve_asset_path(asset: str, page_rel: str, site_url: str) -> str:
    if asset.startswith("http://") or asset.startswith("https://"):
        return replace_foreign_domains(asset, {"site_url": site_url, "old_domain": ""})
    page_dir = Path(page_rel).parent.as_posix()
    if page_dir == ".":
        base = ROOT
    else:
        base = ROOT / page_dir
    if asset.startswith("../"):
        resolved = (base / asset).resolve()
    else:
        resolved = (ROOT / asset).resolve()
    try:
        rel = resolved.relative_to(ROOT).as_posix()
    except ValueError:
        rel = asset.lstrip("./")
    return f"{site_url}/{rel}"


def extract_product_name(text: str, rel: str) -> str | None:
    m = H1_PRODUCT_RE.search(text)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    stem = Path(rel).stem
    if stem != "index":
        return slug_to_title(stem)
    return None


def extract_blog_title(text: str, rel: str) -> str | None:
    m = H1_BLOG_RE.search(text)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    stem = Path(rel).stem
    if stem != "index" and re.search(r"-\d+$", stem):
        return slug_to_title(re.sub(r"-\d+$", "", stem))
    return None


def extract_category_name(old_title: str) -> str | None:
    for pat in OLD_TITLE_PATTERNS:
        m = pat.match(old_title.strip())
        if m:
            return m.group(1).strip()
    return None


HTTRACK_ANY = re.compile(
    r"\n<!-- Mirrored from www\.(?:certifiedglassbottles|spiritsglass)\.com[^>]*-->\s*",
    re.MULTILINE,
)


def remove_httrack(text: str) -> str:
    text = HTTRACK_START.sub("", text)
    text = HTTRACK_END.sub("", text)
    text = HTTRACK_ANY.sub("\n", text)
    return text


def sync_json_ld(text: str, title: str, description: str) -> str:
    m = JSONLD_RE.search(text)
    if not m or not title:
        return text
    payload = m.group(2)
    payload = payload.replace("LIQUORPAC", "KIWL")
    payload = re.sub(
        r'("name"\s*:\s*")(?:[^"\\]|\\.)*(")',
        lambda match, t=title: f'{match.group(1)}{t.replace(chr(34), "")}{match.group(2)}',
        payload,
        count=1,
    )
    if description:
        payload = re.sub(
            r'("description"\s*:\s*")(?:[^"\\]|\\.)*(")',
            lambda match, d=description: f'{match.group(1)}{d.replace(chr(34), "")}{match.group(2)}',
            payload,
            count=1,
        )
    return text[: m.start()] + m.group(1) + payload + m.group(3) + text[m.end() :]


def set_meta(content: str, pattern: re.Pattern[str], new_value: str) -> str:
    return pattern.sub(
        lambda m: m.group(0).replace(m.group(1), new_value.replace('"', "&quot;")),
        content,
        count=1,
    )


def replace_meta_attr(content: str, pattern: re.Pattern[str], new_href: str) -> str:
    if pattern.search(content):
        return pattern.sub(f'\\1{new_href}\\3' if "\\1" in pattern.pattern else new_href, content, count=1)
    return content


def optimize_page(text: str, rel: str, cfg: dict) -> tuple[str, list[str]]:
    changes: list[str] = []
    site_url = cfg["site_url"]
    templates = cfg["templates"]

    before = text
    text = replace_foreign_domains(text, cfg)
    if text != before:
        changes.append("domain")

    text = remove_httrack(text)
    if "HTTrack" in text:
        changes.append("httrack-partial")

    if "LIQUORPAC" in text:
        text = text.replace("LIQUORPAC", cfg["brand"])
        changes.append("brand-global")

    canonical_url = page_url(rel, site_url)
    if CANONICAL_RE.search(text):
        old_can = CANONICAL_RE.search(text).group(1)
        if old_can != canonical_url:
            text = CANONICAL_RE.sub(f'<link rel="canonical" href="{canonical_url}" />', text, count=1)
            changes.append("canonical")
    else:
        text = text.replace("</head>", f'<link rel="canonical" href="{canonical_url}" />\n</head>', 1)
        changes.append("canonical-added")

    def hreflang_repl(m: re.Match[str]) -> str:
        return f'{m.group(1)}{canonical_url}{m.group(3)}'

    new_text = HREFLANG_RE.sub(hreflang_repl, text)
    if new_text != text:
        changes.append("hreflang")
        text = new_text

    og_url_m = OG_URL_RE.search(text)
    if og_url_m and og_url_m.group(1) != canonical_url:
        text = OG_URL_RE.sub(f'<meta property="og:url" content="{canonical_url}" />', text, count=1)
        changes.append("og:url")

    for img_re, label in ((OG_IMAGE_RE, "og:image"), (TWITTER_IMAGE_RE, "twitter:image")):
        m = img_re.search(text)
        if m:
            abs_img = resolve_asset_path(m.group(1), rel, site_url)
            if abs_img != m.group(1):
                text = img_re.sub(f'<meta {"property" if "og" in label else "name"}="{label}" content="{abs_img}" />', text, count=1)
                changes.append(label)

    if TWITTER_CARD_RE.search(text):
        text = TWITTER_CARD_RE.sub(
            '<meta name="twitter:card" content="summary_large_image" />', text, count=1
        )
        changes.append("twitter:card")

    title_m = TITLE_RE.search(text)
    old_title = title_m.group(1).strip() if title_m else ""
    new_title = old_title
    new_desc = DESC_RE.search(text).group(1) if DESC_RE.search(text) else ""
    new_keywords = KEYWORDS_RE.search(text).group(1) if KEYWORDS_RE.search(text) else ""

    rel_posix = rel.replace("\\", "/")

    if rel_posix == "index.html":
        new_title = cfg["homepage"]["title"]
        new_desc = cfg["homepage"]["description"]
        new_keywords = cfg["homepage"]["keywords"]
        changes.append("homepage-seo")
    elif rel_posix == "blog/index.html":
        new_title = cfg["blog_index"]["title"]
        new_desc = cfg["blog_index"]["description"]
        new_keywords = cfg["blog_index"]["keywords"]
        changes.append("blog-index-seo")
    elif rel_posix.startswith("blog/") and rel_posix.endswith(".html") and "/page/" not in rel_posix:
        blog_title = extract_blog_title(text, rel_posix)
        if blog_title:
            new_title = f"{blog_title}{templates['blog_title_suffix']}"
            if len(new_desc) < 80 or new_desc.strip().endswith("?"):
                new_desc = (
                    f"{blog_title}.{templates['blog_description_suffix']}"
                )[:160]
            new_keywords = f"{blog_title.lower()}, bottle caps, packaging, KIWL"
            changes.append("blog-seo")
    elif "prodetails-name" in text or (
        not rel_posix.endswith("/index.html")
        and rel_posix.count("/") >= 1
        and not rel_posix.startswith("showroom/")
        and not rel_posix.startswith("blog/")
    ):
        name = extract_product_name(text, rel_posix)
        if name:
            new_title = templates["product_title"].format(name=name)
            new_desc = templates["product_description"].format(name_lower=name.lower())
            new_keywords = templates["product_keywords"].format(name_lower=name.lower())
            changes.append("product-seo")
    elif rel_posix.startswith("showroom/") and rel_posix.endswith("/index.html"):
        folder = Path(rel_posix).parent.name
        name = slug_to_title(folder)
        new_title = templates["showroom_title"].format(name=name)
        new_desc = templates["showroom_description"].format(name_lower=name.lower())
        new_keywords = templates["showroom_keywords"].format(name_lower=name.lower())
        changes.append("showroom-seo")
    elif rel_posix in {
        "sustainability.html",
        "factory.html",
        "faq.html",
        "about-kiwl.html",
        "about-us.html",
        "contact-us.html",
    }:
        page_name = slug_to_title(Path(rel_posix).stem.replace("-", " "))
        if page_name.lower().startswith("about"):
            page_name = "About KIWL"
        new_title = f"{page_name} | Spirits Glass Packaging Manufacturer - KIWL"
        new_desc = (
            f"Learn about {page_name.lower()} at KIWL, a leading China manufacturer of "
            "spirits glass bottles, caps, stoppers and beverage packaging for global brands."
        )
        new_keywords = f"{page_name.lower()}, KIWL, spirits glass packaging, bottle caps"
        changes.append("static-page-seo")
    elif rel_posix.endswith("/index.html") or (
        rel_posix.endswith(".html") and rel_posix.count("/") == 0
    ):
        page_suffix = ""
        page_m = re.search(r" - Page (\d+)$", old_title, re.I)
        title_for_cat = old_title
        if page_m:
            page_suffix = f" - Page {page_m.group(1)}"
            title_for_cat = old_title[: page_m.start()]
        cat_name = extract_category_name(title_for_cat)
        if rel_posix.startswith("newslist-"):
            new_title = f"Packaging Industry News{page_suffix} | KIWL Blog"
            new_desc = (
                "Latest news and updates on spirits glass bottles, bottle caps and packaging "
                "from KIWL, a leading China manufacturer and exporter."
            )
            new_keywords = "packaging news, bottle cap news, spirits glass, KIWL"
            changes.append("news-seo")
        elif rel_posix.startswith("showroomlist-"):
            new_title = f"Product Showroom{page_suffix} | Spirits Glass Packaging - KIWL"
            new_desc = (
                "Browse KIWL product showroom for wholesale spirits glass bottles, caps, "
                "stoppers and closures for global beverage brands."
            )
            new_keywords = "product showroom, spirits glass, wholesale packaging, KIWL"
            changes.append("showroomlist-seo")
        elif cat_name:
            new_title = templates["category_title"].format(name=cat_name) + page_suffix
            new_desc = templates["category_description"].format(name_lower=cat_name.lower())
            new_keywords = templates["category_keywords"].format(name_lower=cat_name.lower())
            changes.append("category-seo")

    new_title = new_title.replace("LIQUORPAC", cfg["brand"])
    if "LIQUORPAC" in old_title and "LIQUORPAC" not in new_title:
        changes.append("brand-fix")

    if new_title != old_title:
        text = TITLE_RE.sub(f"<title>{new_title}</title>", text, count=1)
    if new_desc and DESC_RE.search(text):
        old_desc = DESC_RE.search(text).group(1)
        if new_desc != old_desc:
            text = DESC_RE.sub(f'<meta name="description" content="{new_desc}" />', text, count=1)
    if new_keywords and KEYWORDS_RE.search(text):
        old_kw = KEYWORDS_RE.search(text).group(1)
        if new_keywords != old_kw:
            text = KEYWORDS_RE.sub(f'<meta name="keywords" content="{new_keywords}" />', text, count=1)

    for tag_re, value in (
        (OG_TITLE_RE, new_title),
        (TWITTER_TITLE_RE, new_title),
        (OG_DESC_RE, new_desc),
        (TWITTER_DESC_RE, new_desc),
    ):
        if value and tag_re.search(text):
            text = tag_re.sub(
                lambda m, v=value: m.group(0).replace(m.group(1), v.replace('"', "&quot;")),
                text,
                count=1,
            )

    if JSONLD_RE.search(text):
        synced = sync_json_ld(text, new_title, new_desc)
        if synced != text:
            text = synced
            changes.append("json-ld-sync")

    return text, changes


def audit_site(cfg: dict) -> list[str]:
    issues: list[str] = []
    html_files = [p for p in ROOT.rglob("*.html") if "_brand_backup" not in str(p)]
    old_domain = cfg["old_domain"]
    site_url = cfg["site_url"]

    missing_canonical = 0
    relative_canonical = 0
    old_domain_refs = 0
    short_desc = 0
    long_title = 0
    httrack = 0
    liquorpac = 0
    duplicate_kw_stuff = 0

    for hf in html_files:
        rel = hf.relative_to(ROOT).as_posix()
        text = hf.read_text(encoding="utf-8", errors="ignore")
        if old_domain in text:
            old_domain_refs += 1
        if "Mirrored from www." in text and "HTTrack" in text:
            httrack += 1
        if "LIQUORPAC" in text:
            liquorpac += 1
        cm = CANONICAL_RE.search(text)
        if not cm:
            missing_canonical += 1
        elif not cm.group(1).startswith("http"):
            relative_canonical += 1
        tm = TITLE_RE.search(text)
        if tm and len(tm.group(1)) > 60:
            long_title += 1
        dm = DESC_RE.search(text)
        if dm and len(dm.group(1)) < 50:
            short_desc += 1
        if tm and "Manufacturers Suppliers Factory" in tm.group(1):
            duplicate_kw_stuff += 1

    issues.extend(
        [
            f"Total HTML pages: {len(html_files)}",
            f"Old domain ({old_domain}) references: {old_domain_refs}",
            f"HTTrack comments remaining: {httrack}",
            f"LIQUORPAC brand refs: {liquorpac}",
            f"Missing canonical: {missing_canonical}",
            f"Relative canonical URLs: {relative_canonical}",
            f"Titles over 60 chars: {long_title}",
            f"Descriptions under 50 chars: {short_desc}",
            f"Keyword-stuffed titles (Manufacturers Suppliers Factory): {duplicate_kw_stuff}",
            "",
            "=== Google Algorithm Compliance Notes ===",
            "- meta keywords: Google ignores since 2009; kept for Bing/Yandex only",
            "- Title/description/structured data: primary ranking signals",
            "- Absolute canonical URLs: required to avoid duplicate content",
            "- JSON-LD Organization/Product: helps rich results",
            "- Blog thin meta descriptions: improved where possible",
            "",
            f"Target site URL: {site_url}",
            f"Primary keywords: {', '.join(cfg['primary_keywords'][:5])}...",
        ]
    )
    return issues


def main() -> None:
    cfg = load_config()
    stats: dict[str, int] = {}
    changed_files = 0

    html_files = sorted(
        p for p in ROOT.rglob("*.html") if "_brand_backup" not in str(p)
    )

    print("=== Before optimization ===")
    before = audit_site(cfg)
    print("\n".join(before))

    for hf in html_files:
        rel = hf.relative_to(ROOT).as_posix()
        original = hf.read_text(encoding="utf-8", errors="ignore")
        updated, changes = optimize_page(original, rel, cfg)
        if updated != original:
            hf.write_text(updated, encoding="utf-8")
            changed_files += 1
            for c in changes:
                stats[c] = stats.get(c, 0) + 1

    robots = ROOT / "robots.txt"
    if robots.exists():
        robots.write_text(
            "User-agent: *\nAllow: /\n\nSitemap: "
            f"{cfg['site_url']}/sitemap.xml\n",
            encoding="utf-8",
        )
        stats["robots.txt"] = 1

    sitemap = ROOT / "sitemap.xml"
    if sitemap.exists():
        sm = sitemap.read_text(encoding="utf-8", errors="ignore")
        sm_new = replace_foreign_domains(sm, cfg)
        if sm_new != sm:
            sitemap.write_text(sm_new, encoding="utf-8")
            stats["sitemap.xml"] = 1

    js_float = ROOT / "Content" / "File_Img" / "11134" / "float11134.js"
    if js_float.exists():
        js = js_float.read_text(encoding="utf-8", errors="ignore")
        js_new = replace_foreign_domains(js, cfg)
        if js_new != js:
            js_float.write_text(js_new, encoding="utf-8")
            stats["float.js"] = 1

    print("\n=== After optimization ===")
    after = audit_site(cfg)
    print("\n".join(after))

    print(f"\nChanged HTML files: {changed_files}/{len(html_files)}")
    print("Change breakdown:", dict(sorted(stats.items(), key=lambda x: -x[1])))

    report = [
        f"SEO OPTIMIZATION REPORT - {cfg['site_url']}",
        "=" * 50,
        "",
        "--- BEFORE ---",
        *before,
        "",
        "--- AFTER ---",
        *after,
        "",
        "--- CHANGES ---",
        f"HTML files modified: {changed_files}",
        json.dumps(stats, indent=2),
        "",
        "--- KEYWORD STRATEGY ---",
        "Tier 1 (Homepage): spirits glass bottles, liquor bottle caps, aluminium screw caps",
        "Tier 2 (Categories): bottle cap, bottle stopper, liquor bottles, metal label",
        "Tier 3 (Products): long-tail product names + wholesale + manufacturer",
        "Tier 4 (Blog): question-based queries linking to product categories",
        "",
        "--- RECOMMENDED NEXT STEPS ---",
        f"1. Submit sitemap in Google Search Console for {cfg['site_url']}",
        "2. If www.spiritsglass.com is used for staging, block it from indexing (noindex or robots disallow)",
        "3. Add unique product descriptions (avoid duplicate factory boilerplate in body)",
        "4. Compress images and add width/height attributes for Core Web Vitals",
        "5. Consider noindex for /showroom/ tag pages if they duplicate product categories",
        "6. Build backlinks from packaging industry directories",
    ]
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"\nReport saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
