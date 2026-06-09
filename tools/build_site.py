#!/usr/bin/env python3
import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "liusijiastar.WordPress.2026-06-09.xml"
SITE_TITLE = "LIU SIJIA STAR"
NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}

PRIMARY = ["about", "publication", "artwork", "experiences"]
SLUG_ALIASES = {"__trashed-6": "to-summer"}
PAGE_ID_TO_SLUG = {
    "204": "to-summer",
    "253": "diving-into-the-unknown",
    "275": "in-active",
    "283": "fortune-telling",
    "303": "what-kind-of-world-flows-from-beehive",
    "312": "where-shall-we-meet-tonight",
    "323": "look-deep-into-your-dream",
    "330": "secret-recycling",
}
PROJECTS = [
    "speculative-visions-of-a-post-climate-future",
    "dreamscapes",
    "nonhumotion",
    "future-tense",
    "dreamscaping",
    "time-enough",
    "diving-into-the-unknown",
    "to-summer",
    "in-active",
    "secret-recycling",
    "where-shall-we-meet-tonight",
    "what-kind-of-world-flows-from-beehive",
    "fortune-telling",
    "look-deep-into-your-dream",
]
DISPLAY_TITLES = {
    "to-summer": "To Summer Commercial Project",
}
CARD_COVERS = {
    "time-enough": None,
    "look-deep-into-your-dream": "2024/04/2-7.jpg",
}
POSTER_CARDS = {
    "speculative-visions-of-a-post-climate-future",
    "dreamscapes",
    "future-tense",
}


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
        slug = SLUG_ALIASES.get(slug, slug)
        title = (item.findtext("title") or slug).strip()
        content = text(item, "content:encoded")
        pages.append({"slug": slug, "title": title, "content": content})
    return {page["slug"]: page for page in pages}


def clean_content(markup, prefix=""):
    markup = markup.replace("u002d", "-")
    markup = re.sub(r"<!--\s*/?wp:[\s\S]*?-->", "", markup)
    markup = re.sub(r"<header[\s\S]*?</header>", "", markup, count=1)
    markup = re.sub(r"<div[^>]+class=\"wp-block-spacer\"[^>]*></div>", "", markup)
    markup = re.sub(r"<p[^>]*>\s*<a href=\"https://www.instagram.com/starliusijia/\"[\s\S]*?</p>", "", markup)
    markup = re.sub(r"<div class=\"wp-block-group alignfull\"[^>]*>\s*<div class=\"wp-block-group\"[^>]*>\s*<div class=\"wp-block-group\"></div>\s*</div>\s*</div>", "", markup)
    markup = re.sub(r"https://starliusijiacom\.wordpress\.com/wp-content/uploads/", "", markup)
    markup = re.sub(r"https://starliusijia\.com/wp-content/uploads/", "", markup)
    markup = re.sub(r'https://starliusijia\.com/([^"/?#]+)/?', lambda m: f'{prefix}{m.group(1)}/index.html', markup)
    markup = re.sub(r'https://starliusijiacom\.wordpress\.com/\?page_id=(\d+)', lambda m: f'{prefix}{PAGE_ID_TO_SLUG.get(m.group(1), "artwork")}/index.html', markup)
    markup = re.sub(r"((?:src|href)=\"[^\"]+?)\?w=\d+", r"\1", markup)
    if prefix:
        markup = re.sub(r'((?:src|href)=")(20\d{2}/)', rf"\1{prefix}\2", markup)
    markup = re.sub(r"\s(?:width|height|sizes|srcset)=\"[^\"]*\"", "", markup)
    markup = re.sub(r"\sstyle=\"[^\"]*\"", "", markup)
    markup = re.sub(
        r"<figure class=\"wp-block-embed[\s\S]*?<div class=\"wp-block-embed__wrapper\">\s*(https?://[^\s<]+)\s*</div></figure>",
        lambda match: video_embed(match.group(1)),
        markup,
    )
    markup = re.sub(r"<div class=\"wp-block-group alignfull\"[^>]*>\s*</div>", "", markup)
    return markup.strip()


def excerpt(markup, limit=170):
    plain = re.sub(r"<[^>]+>", " ", clean_content(markup))
    plain = html.unescape(re.sub(r"\s+", " ", plain)).strip()
    return plain[:limit].rsplit(" ", 1)[0] + ("..." if len(plain) > limit else "")


def video_embed(url):
    clean_url = html.unescape(url)
    parsed = urlparse(clean_url)
    host = parsed.netloc.lower()
    if "youtube.com" in host:
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        if video_id:
            return video_iframe(f"https://www.youtube.com/embed/{html.escape(video_id)}", "Embedded YouTube video")
    if "youtu.be" in host:
        video_id = parsed.path.strip("/").split("/")[0]
        if video_id:
            return video_iframe(f"https://www.youtube.com/embed/{html.escape(video_id)}", "Embedded YouTube video")
    if "vimeo.com" in host:
        match = re.search(r"/(\d+)", parsed.path)
        if match:
            return video_iframe(f"https://player.vimeo.com/video/{html.escape(match.group(1))}", "Embedded Vimeo video")
    escaped = html.escape(clean_url)
    return f'<p class="media-link"><a href="{escaped}">{escaped}</a></p>'


def video_iframe(src, title):
    return (
        '<div class="video-embed">'
        f'<iframe src="{src}" title="{title}" loading="lazy" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
        "allowfullscreen></iframe></div>"
    )


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
    home_image = "assets/home-cat-moon.png" if (ROOT / "assets" / "home-cat-moon.png").exists() else "2024/04/star-edited.jpg"
    body = """<section class="home-clean">
  <div class="home-image">
    <img src="{home_image}" alt="Night sea illustration with a white cat under the moon">
  </div>
  <div class="home-name">
    <h1><span>LIU</span><span>Sijia Star</span></h1>
    <p>Art, Design, Curation, Research</p>
  </div>
</section>""".format(home_image=home_image)
    return shell("home", SITE_TITLE, body)


def build_artwork_page(pages):
    cards = []
    for slug in PROJECTS:
        page = pages.get(slug)
        if not page:
            continue
        image = CARD_COVERS.get(slug, first_image(page["content"]))
        year_match = re.search(r"<p[^>]*>\s*((?:19|20)\d{2}(?:[-–](?:19|20)?\d{2})?)\s*</p>", clean_content(page["content"]))
        year = year_match.group(1) if year_match else ""
        title = DISPLAY_TITLES.get(slug, page["title"].replace("\xa0", " ").strip())
        image_html = f'<img src="../{image}" alt="">' if image else '<span class="text-cover">TIME<br>ENOUGH</span>'
        card_classes = "art-card"
        if slug in POSTER_CARDS:
            card_classes += " is-poster"
        if not image:
            card_classes += " is-text-cover"
        cards.append(
            f"""<a class="{card_classes}" href="../{slug}/index.html">
  <span class="art-thumb">{image_html}</span>
  <span class="art-title">{html.escape(title)}</span>
  <span class="art-year">{html.escape(year)}</span>
</a>"""
        )
    body = f"""<section class="artwork-page">
  <h1>Art</h1>
  <div class="art-grid">{''.join(cards)}</div>
</section>"""
    return shell("artwork", "Art", body, "Selected artwork and curatorial projects.")


def build_standard_page(page):
    prefix = rel_prefix(page["slug"])
    content = clean_content(page["content"], prefix)
    content = re.sub(r"^\s*<div class=\"wp-block-columns[^>]*>\s*<div class=\"wp-block-column\">\s*<h1[^>]*>Publications</h1>[\s\S]*?</div>\s*<div class=\"wp-block-column\"></div>\s*</div>", "", content, count=1)
    page_class = f"page page-{page['slug']}"
    title = DISPLAY_TITLES.get(page["slug"], page["title"].replace("\xa0", " ").strip())
    content = re.sub(r"To Summer Offline Shop Projects", "To Summer Commercial Project", content)
    content = re.sub(
        rf'^\s*<div class="wp-block-group[^"]*">\s*<div class="wp-block-columns[^"]*">\s*<div class="wp-block-column[^"]*">\s*<h2 class="wp-block-heading">{re.escape(title)}</h2>',
        lambda _m: _m.group(0).replace(f'<h2 class="wp-block-heading">{title}</h2>', ""),
        content,
        count=1,
    )
    body = f"""<article class="page">
  <h1>{html.escape(title)}</h1>
  <div class="wp-content">{content}</div>
</article>"""
    body = body.replace('class="page"', f'class="{page_class}"', 1)
    return shell(page["slug"], title, body, excerpt(page["content"]))


def main():
    pages = load_pages()
    (ROOT / "assets").mkdir(exist_ok=True)
    write_page("home", build_home(pages))
    for slug, page in pages.items():
        if slug == "artwork":
            write_page(slug, build_artwork_page(pages))
            continue
        write_page(slug, build_standard_page(page))


if __name__ == "__main__":
    main()
