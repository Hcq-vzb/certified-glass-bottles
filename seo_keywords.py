#!/usr/bin/env python3
"""Pyramid keyword strategy resolver for KIWL static site SEO."""

from __future__ import annotations

import re
from pathlib import Path

PRODUCT_ROOTS = {
    "bottle-cap",
    "liquor-bottles",
    "bottle-stopper",
    "metal-label",
    "paper-box",
}

BLOG_TOPIC_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"wine|screw cap|ropp|gpi|closure|cap cover|bottle cap", re.I), "bottle-cap"),
    (re.compile(r"glass bottle|liquor bottle|vodka|whisky|whiskey|gin|spirits bottle|wine bottle", re.I), "liquor-bottles"),
    (re.compile(r"stopper|cork|plug", re.I), "bottle-stopper"),
    (re.compile(r"label|sticker", re.I), "metal-label"),
    (re.compile(r"paper box|paper tube|packaging box", re.I), "paper-box"),
]


def slug_to_title(slug: str) -> str:
    return " ".join(word.capitalize() for word in slug.replace("-", " ").split())


def fit_len(text: str, max_len: int = 160) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(".,;:") + "…"


def fit_title_len(title: str, max_len: int = 60) -> str:
    title = re.sub(r"\s+", " ", title.strip())
    if len(title) <= max_len:
        return title
    for suffix in (" | KIWL Packaging Blog", " | KIWL", " - KIWL"):
        if suffix in title:
            name = title[: title.rfind(suffix)].strip(" -|")
            room = max_len - len(suffix)
            if room >= 20:
                trimmed = name[:room]
                if " " in trimmed:
                    trimmed = trimmed.rsplit(" ", 1)[0]
                return f"{trimmed.rstrip(' -|,&')}{suffix}"
    cut = title[: max_len - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" -|,&") + "…"


def _tier2_cfg(cfg: dict) -> dict:
    return cfg.get("keyword_pyramid", {}).get("tier2", {})


def _tier3_cfg(cfg: dict) -> dict:
    return cfg.get("keyword_pyramid", {}).get("tier3", {})


def _templates(cfg: dict) -> dict:
    base = cfg.get("templates", {})
    pyramid = cfg.get("keyword_pyramid", {}).get("templates", {})
    return {**base, **pyramid}


def classify_page(rel: str) -> dict:
    rel = rel.replace("\\", "/")
    parts = [p for p in rel.split("/") if p]

    if rel == "index.html":
        return {"tier": 1, "kind": "homepage"}
    if rel in cfg_static_hint(rel):
        return {"tier": 2, "kind": "static", "path": rel}
    if rel == "blog/index.html":
        return {"tier": 5, "kind": "blog_index"}
    if rel.startswith("blog/page/") and rel.endswith("/index.html"):
        return {"tier": 5, "kind": "blog_page"}
    if rel.startswith("blog/") and rel.endswith(".html"):
        return {"tier": 5, "kind": "blog_article"}
    if rel.startswith("newslist-"):
        return {"tier": 5, "kind": "news"}
    if rel.startswith("news/") and rel.endswith(".html"):
        return {"tier": 5, "kind": "news_article"}
    if rel.startswith("showroomlist-"):
        return {"tier": 6, "kind": "showroom_list"}
    if rel.startswith("showroom/") and rel.endswith("/index.html"):
        return {"tier": 6, "kind": "showroom_tag"}

    if parts and parts[0] in PRODUCT_ROOTS:
        if rel.endswith("/index.html"):
            cat_path = rel.removesuffix("/index.html").rstrip("/")
            segs = [s for s in cat_path.split("/") if s]
            if len(segs) == 1:
                return {"tier": 2, "kind": "category", "root": segs[0], "path": cat_path}
            if len(segs) == 2:
                return {
                    "tier": 3,
                    "kind": "subcategory",
                    "root": segs[0],
                    "path": cat_path,
                    "slug": segs[1],
                }
        elif rel.endswith(".html") and len(parts) >= 2:
            root = parts[0]
            if len(parts) == 2:
                return {
                    "tier": 4,
                    "kind": "product",
                    "root": root,
                    "path": root,
                    "slug": Path(rel).stem,
                }
            return {
                "tier": 4,
                "kind": "product",
                "root": root,
                "path": f"{parts[0]}/{parts[1]}",
                "slug": Path(rel).stem,
            }

    if rel.endswith("/index.html") or (rel.endswith(".html") and rel.count("/") == 0):
        return {"tier": 2, "kind": "generic_category"}

    return {"tier": 0, "kind": "other"}


def cfg_static_hint(rel: str) -> set[str]:
    return {
        "products.html",
        "factory.html",
        "faq.html",
        "about-kiwl.html",
        "about-us.html",
        "contact-us.html",
        "sustainability.html",
        "inquiry.html",
        "decorating-finishing.html",
        "in-house-molding.html",
        "lean-manufacturing.html",
        "quality-management.html",
        "custom-lid-label-paper-box.html",
        "manufacturing.html",
        "packaging.html",
        "delivery-warehousing.html",
        "project-management.html",
        "service.html",
        "media.html",
    }


def blog_category_hint(title: str, cfg: dict) -> str | None:
    for pattern, root in BLOG_TOPIC_RULES:
        if pattern.search(title):
            tier2 = _tier2_cfg(cfg).get(root, {})
            return tier2.get("primary", root.replace("-", " "))
    return None


def lookup_tier3(path: str, cfg: dict) -> dict | None:
    tier3 = _tier3_cfg(cfg)
    if path in tier3:
        return tier3[path]
    return None


def lookup_tier2(root: str, cfg: dict) -> dict | None:
    tier2 = _tier2_cfg(cfg)
    if root in tier2:
        return tier2[root]
    return None


def extract_product_name(text: str, rel: str) -> str | None:
    m = re.search(r'<h1 class="prodetails-name">(.*?)</h1>', text, re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    stem = Path(rel).stem
    if stem != "index":
        return slug_to_title(stem)
    return None


def extract_category_name(text: str, rel: str) -> str | None:
    m = re.search(r'<h1 class="banner-title-h1">(.*?)</h1>', text, re.DOTALL)
    if m:
        name = re.sub(r"\s+", " ", m.group(1)).strip()
        if name and name.lower() not in {"products", "product categories"}:
            return name
    path = rel.replace("\\", "/")
    if path.endswith("/index.html"):
        slug = path.split("/")[-2] if "/" in path else Path(path).parent.name
        if slug and slug != "index":
            return slug_to_title(slug)
    return None


def resolve_pyramid_meta(
    rel: str,
    cfg: dict,
    text: str = "",
    current_title: str = "",
) -> dict | None:
    """Return {title, description, keywords, tier, tier_label} or None."""
    info = classify_page(rel)
    tier = info.get("tier", 0)
    templates = _templates(cfg)
    brand = cfg.get("brand", "KIWL")
    pyramid = cfg.get("keyword_pyramid", {})

    if tier == 1:
        hp = cfg.get("homepage", {})
        t1 = pyramid.get("tier1", {})
        return {
            "tier": 1,
            "tier_label": t1.get("label", "Brand Head Terms"),
            "title": hp.get("title", current_title),
            "description": hp.get("description", ""),
            "keywords": hp.get("keywords") or ", ".join(
                [t1.get("primary", "")] + t1.get("secondary", [])[:4] + [brand]
            ),
        }

    if info["kind"] == "static":
        page = cfg.get("static_pages", {}).get(rel, {})
        if page:
            return {
                "tier": 2,
                "tier_label": "Supporting Pages",
                "title": page.get("title", current_title),
                "description": page.get("description", ""),
                "keywords": page.get("keywords", ""),
            }

    if info["kind"] == "blog_index":
        bi = cfg.get("blog_index", {})
        t5 = pyramid.get("tier5", {})
        return {
            "tier": 5,
            "tier_label": t5.get("label", "Content Long-tail"),
            "title": bi.get("title", current_title),
            "description": bi.get("description", ""),
            "keywords": bi.get("keywords", ""),
        }

    if info["kind"] == "blog_page":
        page_m = re.search(r"page/(\d+)/", rel)
        page_num = page_m.group(1) if page_m else "1"
        desc_tpl = cfg.get(
            "blog_page_description",
            "Page {page} of the KIWL packaging blog with expert guides on wine screw caps and spirits packaging.",
        )
        return {
            "tier": 5,
            "tier_label": "Content Long-tail",
            "title": current_title or f"Packaging Blog - Page {page_num} | KIWL",
            "description": fit_len(desc_tpl.format(page=page_num)),
            "keywords": f"packaging blog page {page_num}, bottle cap guides, spirits glass tips, {brand}",
        }

    if info["kind"] == "blog_article":
        blog_title = current_title.replace(" | KIWL Packaging Blog", "").strip()
        if not blog_title:
            m = re.search(r'<h1 class="newscontent-title">(.*?)</h1>', text, re.DOTALL)
            if m:
                blog_title = re.sub(r"\s+", " ", m.group(1)).strip()
        related = blog_category_hint(blog_title, cfg) or "spirits packaging"
        t5 = pyramid.get("tier5", {})
        suffix = templates.get(
            "blog_description_suffix",
            " Learn from KIWL, a leading spirits and beverage packaging manufacturer in China.",
        )
        kw_tpl = t5.get(
            "blog_keywords",
            "{topic}, {related}, packaging guide, wholesale manufacturer, {brand}",
        )
        return {
            "tier": 5,
            "tier_label": t5.get("label", "Content Long-tail"),
            "title": fit_title_len(f"{blog_title} | KIWL Packaging Blog") if blog_title else current_title,
            "description": fit_len(f"{blog_title}.{suffix}" if blog_title else ""),
            "keywords": kw_tpl.format(
                topic=blog_title.lower() if blog_title else "packaging",
                related=related,
                brand=brand,
            ),
        }

    if info["kind"] == "news":
        return {
            "tier": 5,
            "tier_label": "Industry News",
            "title": current_title,
            "description": fit_len(
                "Latest packaging industry news on spirits glass bottles, aluminium screw caps "
                f"and beverage closures from {brand}, China manufacturer and exporter."
            ),
            "keywords": f"packaging industry news, bottle cap news, spirits glass, {brand}",
        }

    if info["kind"] in {"showroom_list", "showroom_tag"}:
        t6 = pyramid.get("tier6", {})
        name = slug_to_title(info.get("path", rel).split("/")[-1].replace("-", " "))
        if info["kind"] == "showroom_list":
            return {
                "tier": 6,
                "tier_label": t6.get("label", "Showroom Discovery"),
                "title": current_title,
                "description": fit_len(
                    "Browse KIWL product showroom for wholesale spirits glass bottles, aluminium caps "
                    "and closures for global beverage brands."
                ),
                "keywords": f"product showroom, spirits glass packaging, wholesale, {brand}",
            }
        return {
            "tier": 6,
            "tier_label": t6.get("label", "Showroom Discovery"),
            "title": current_title,
            "description": fit_len(
                f"Explore {name.lower()} packaging solutions from {brand}. "
                "Wholesale glass bottles, caps and closures for liquor, wine and beverage brands."
            ),
            "keywords": f"{name.lower()}, spirits glass packaging, wholesale, {brand}",
        }

    if info["kind"] == "category":
        root = info["root"]
        t2 = lookup_tier2(root, cfg) or {}
        name = t2.get("name") or extract_category_name(text, rel) or slug_to_title(root)
        name_lower = name.lower()
        primary = t2.get("primary", name_lower)
        return {
            "tier": 2,
            "tier_label": pyramid.get("tier2_label", "Category Keywords"),
            "title": t2.get("title") or fit_title_len(
                templates.get("category_title", "{name} Wholesale | Custom Packaging - KIWL").format(name=name)
            ),
            "description": fit_len(
                t2.get("description")
                or templates.get(
                    "category_description",
                    "Browse wholesale {name_lower} from KIWL. Professional manufacturer and exporter "
                    "of spirits, wine and beverage packaging. Bulk orders, custom branding, worldwide shipping.",
                ).format(name=name, name_lower=name_lower, primary=primary)
            ),
            "keywords": t2.get("keywords") or templates.get(
                "category_keywords",
                "{name_lower}, wholesale {name_lower}, {primary}, China supplier, {brand}",
            ).format(name=name, name_lower=name_lower, primary=primary, brand=brand),
        }

    if info["kind"] == "subcategory":
        path = info["path"]
        root = info["root"]
        t3 = lookup_tier3(path, cfg) or {}
        t2 = lookup_tier2(root, cfg) or {}
        name = t3.get("name") or extract_category_name(text, rel) or slug_to_title(info.get("slug", ""))
        name_lower = name.lower()
        primary = t3.get("primary") or t2.get("primary", name_lower)
        tier2_primary = t2.get("primary", root.replace("-", " "))
        return {
            "tier": 3,
            "tier_label": pyramid.get("tier3_label", "Subcategory Keywords"),
            "title": t3.get("title") or fit_title_len(
                templates.get(
                    "subcategory_title",
                    "{name} Wholesale | {primary} - KIWL",
                ).format(name=name, primary=primary.title(), name_lower=name_lower)
            ),
            "description": fit_len(
                t3.get("description")
                or templates.get(
                    "subcategory_description",
                    "Wholesale {name_lower} and {primary} from KIWL. Custom OEM/ODM {tier2_primary}, "
                    "bulk orders, factory-direct pricing and export to 70+ countries.",
                ).format(
                    name=name,
                    name_lower=name_lower,
                    primary=primary,
                    tier2_primary=tier2_primary,
                    brand=brand,
                )
            ),
            "keywords": t3.get("keywords") or templates.get(
                "subcategory_keywords",
                "{name_lower}, wholesale {name_lower}, {primary}, {tier2_primary}, China manufacturer, {brand}",
            ).format(
                name=name,
                name_lower=name_lower,
                primary=primary,
                tier2_primary=tier2_primary,
                brand=brand,
            ),
        }

    if info["kind"] == "product":
        path = info.get("path", info["root"])
        root = info["root"]
        t3 = lookup_tier3(path, cfg)
        if not t3 and "/" not in path:
            t2 = lookup_tier2(root, cfg) or {}
            tier3_primary = t2.get("primary", slug_to_title(root).lower())
            tier2_name = t2.get("name", slug_to_title(root))
        else:
            t3 = t3 or {}
            t2 = lookup_tier2(root, cfg) or {}
            tier3_primary = t3.get("primary", t2.get("primary", ""))
            tier2_name = t2.get("name", slug_to_title(root))

        name = extract_product_name(text, rel) or slug_to_title(info.get("slug", ""))
        name_lower = name.lower()
        t4 = pyramid.get("tier4", {})
        title_tpl = templates.get(
            "product_title",
            "{name} | {tier3_primary} Wholesale - KIWL",
        )
        desc_tpl = templates.get(
            "product_description",
            "Wholesale {name_lower} — {tier3_primary} from KIWL. Custom OEM/ODM {tier2_name_lower}, "
            "competitive factory pricing and export to 70+ countries.",
        )
        kw_tpl = templates.get(
            "product_keywords",
            "{name_lower}, wholesale {name_lower}, {tier3_primary}, {tier2_primary}, China manufacturer, {brand}",
        )
        return {
            "tier": 4,
            "tier_label": t4.get("label", "Product Long-tail"),
            "title": fit_title_len(
                title_tpl.format(
                    name=name,
                    tier3_primary=tier3_primary.title(),
                    name_lower=name_lower,
                )
            ),
            "description": fit_len(
                desc_tpl.format(
                    name=name,
                    name_lower=name_lower,
                    tier3_primary=tier3_primary,
                    tier2_name=tier2_name,
                    tier2_name_lower=tier2_name.lower(),
                    brand=brand,
                )
            ),
            "keywords": kw_tpl.format(
                name=name,
                name_lower=name_lower,
                tier3_primary=tier3_primary,
                tier2_primary=t2.get("primary", tier2_name.lower()),
                brand=brand,
            ),
        }

    return None
