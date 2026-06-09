#!/usr/bin/env python3
import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "liusijiastar.WordPress.2026-06-09.xml"
SITE_TITLE = "LIU SIJIA STAR"
NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}

PRIMARY = ["about", "publication", "artwork", "experiences"]
PROJECTS = [
    "nonhumotion",
    "dreamscapes",
    "speculative-visions-of-a-post-climate-future",
    "future-tense",
    "dreamscaping",
    "time-enough",
    "secret-recycling",
    "look-deep-into-your-dream",
    "where-shall-we-meet-tonight",
    "what-kind-of-world-flows-from-beehive",
    "fortune-telling",
    "in-active",
    "diving-into-the-unknown",
]


def text(node, query, default=""):
    value = node.findtext(query, namespaces=NS)
    return value if value is not None else default


def load_pages():
    root = ET.parse(EXPORT).getroot()
    pages = []
    for item in root.find("channel").findall("item"):
        if text(item, "wp:post_type") != "page" or text(item, "wp:status") != "publish":
            continue
        slug = text(item, "wp:post_name").strip()
        title = (item.findtext("title") or slug).strip()
        content = text(item, "content:encoded")
        pages.append({"slug": slug, "title": title, "content": content})
    return {page["slug"]: page for page in pages}


def clean_content(markup, prefix=""):
    markup = markup.replace("u002d", "-")
    markup = re.sub(r"<!--\s*/?wp:[\s\S]*?-->", "", markup)
    markup = re.sub(r"<header[\s\S]*?</header>", "", markup, count=1)
    markup = re.sub(r"<p[^>]*>\s*<a href=\"https://www.instagram.com/starliusijia/\"[\s\S]*?</p>", "", markup)
    markup = re.sub(r"<div class=\"wp-block-group alignfull\"[^>]*>\s*<div class=\"wp-block-group\"[^>]*>\s*<div class=\"wp-block-group\"></div>\s*</div>\s*</div>", "", markup)
    markup = re.sub(r"https://starliusijiacom\.wordpress\.com/wp-content/uploads/", "", markup)
    markup = re.sub(r"https://starliusijia\.com/wp-content/uploads/", "", markup)
    markup = re.sub(r"((?:src|href)=\"[^\"]+?)\?w=\d+", r"\1", markup)
    if prefix:
        markup = re.sub(r'((?:src|href)=")(20\d{2}/)', rf"\1{prefix}\2", markup)
    markup = re.sub(r"\s(?:width|height|sizes|srcset)=\"[^\"]*\"", "", markup)
    markup = re.sub(r"<div class=\"wp-block-group alignfull\"[^>]*>\s*</div>", "", markup)
    return markup.strip()


def excerpt(markup, limit=170):
    plain = re.sub(r"<[^>]+>", " ", clean_content(markup))
    plain = html.unescape(re.sub(r"\s+", " ", plain)).strip()
    return plain[:limit].rsplit(" ", 1)[0] + ("..." if len(plain) > limit else "")


def first_image(markup):
    match = re.search(r"<img[^>]+src=\"([^\"]+)\"", clean_content(markup))
    return match.group(1) if match else ""


def href_for(slug):
    return "index.html" if slug == "home" else f"{slug}/index.html"


def rel_prefix(slug):
    return "" if slug == "home" else "../"


def nav(slug):
    prefix = rel_prefix(slug)
    links = [("Home", prefix + "index.html")]
    links += [(label.title(), prefix + f"{label}/index.html") for label in PRIMARY]
    return "".join(f'<a href="{url}">{label}</a>' for label, url in links)


def shell(slug, title, body, description=""):
    prefix = rel_prefix(slug)
    page_title = SITE_TITLE if slug == "home" else f"{html.escape(title)} | {SITE_TITLE}"
    desc = html.escape(description or "Portfolio website for artist and designer Liu Sijia Star.")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{desc}">
  <title>{page_title}</title>
  <link rel="stylesheet" href="{prefix}assets/site.css">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="{prefix}index.html">{SITE_TITLE}</a>
    <nav aria-label="Main navigation">{nav(slug)}</nav>
  </header>
  <main>{body}</main>
  <footer class="site-footer">
    <a href="https://www.instagram.com/starliusijia/">Instagram</a>
    <a href="mailto:starliu514@gmail.com">Email</a>
    <a href="http://www.linkedin.com/in/star-liu-130547100/">LinkedIn</a>
  </footer>
</body>
</html>
"""


def write_page(slug, content):
    if slug == "home":
        path = ROOT / "index.html"
    else:
        path = ROOT / slug / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_home(pages):
    cards = []
    for slug in PROJECTS:
        page = pages.get(slug)
        if not page:
            continue
        image = first_image(page["content"])
        image_html = f'<img src="{image}" alt="">' if image else ""
        cards.append(
            f"""<a class="project-card" href="{slug}/index.html">
  {image_html}
  <span>{html.escape(page["title"])}</span>
</a>"""
        )
    body = f"""<section class="home-hero">
  <p>Artist, researcher, and experience designer</p>
  <h1>{SITE_TITLE}</h1>
</section>
<section class="project-grid" aria-label="Selected projects">
  {''.join(cards)}
</section>"""
    return shell("home", SITE_TITLE, body)


def build_standard_page(page):
    prefix = rel_prefix(page["slug"])
    body = f"""<article class="page">
  <h1>{html.escape(page["title"])}</h1>
  <div class="wp-content">{clean_content(page["content"], prefix)}</div>
</article>"""
    return shell(page["slug"], page["title"], body, excerpt(page["content"]))


def main():
    pages = load_pages()
    (ROOT / "assets").mkdir(exist_ok=True)
    write_page("home", build_home(pages))
    for slug, page in pages.items():
        if slug.startswith("__trashed"):
            continue
        write_page(slug, build_standard_page(page))


if __name__ == "__main__":
    main()
