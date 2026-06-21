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
NAV_LABELS = {"artwork": "Art"}
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
    "time-enough": "assets/time-enough-installation-1.png",
    "look-deep-into-your-dream": "2024/04/2-7.jpg",
}
POSTER_CARDS = {
    "speculative-visions-of-a-post-climate-future",
    "dreamscapes",
    "future-tense",
}
VENUE_DETAILS = {
    "speculative-visions-of-a-post-climate-future": (
        "Korean Cultural Center in Hong Kong, Central, Hong Kong"
    ),
    "dreamscapes": "Pao Galleries, Hong Kong Arts Centre, Wan Chai, Hong Kong",
    "future-tense": "Pao Galleries, Hong Kong Arts Centre, Wan Chai, Hong Kong",
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
    markup = markup.replace(
        "2025/04/083e650eb4741b89e5d837f463b6a8ca.png",
        "2025/04/083e650eb4741b89e5d837f463b6a8ca%20copy.jpg",
    )
    markup = markup.replace(
        "https://doi.org/10.48550/arXiv.2604.25657",
        "https://doi.org/10.1145/3800645.3812941",
    )
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
    markup = shorten_link_text(markup)
    markup = re.sub(r"<div class=\"wp-block-group alignfull\"[^>]*>\s*</div>", "", markup)
    return markup.strip()


def excerpt(markup, limit=170):
    plain = re.sub(r"<[^>]+>", " ", normalize_dates(clean_content(markup)))
    plain = html.unescape(re.sub(r"\s+", " ", plain)).strip()
    return plain[:limit].rsplit(" ", 1)[0] + ("..." if len(plain) > limit else "")


def video_embed(url):
    clean_url = html.unescape(url)
    start_at = None
    if clean_url in {"https://youtu.be/qMnxyR7JGao", "https://www.youtube.com/watch?v=qMnxyR7JGao"}:
        clean_url = "https://www.youtube.com/watch?v=qMnxyR7JGao"
        start_at = "3"
    parsed = urlparse(clean_url)
    host = parsed.netloc.lower()
    if "youtube.com" in host:
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        if video_id:
            embed_host = "www.youtube.com" if video_id == "qMnxyR7JGao" else "www.youtube-nocookie.com"
            src = f"https://{embed_host}/embed/{html.escape(video_id)}"
            if start_at:
                src += f"?start={html.escape(start_at)}"
            return video_iframe(
                src,
                "Embedded YouTube video",
                clean_url,
                "Watch on YouTube",
                "video-container" if start_at else "video-embed",
            )
    if "youtu.be" in host:
        video_id = parsed.path.strip("/").split("/")[0]
        if video_id:
            embed_host = "www.youtube.com" if video_id == "qMnxyR7JGao" else "www.youtube-nocookie.com"
            src = f"https://{embed_host}/embed/{html.escape(video_id)}"
            if start_at:
                src += f"?start={html.escape(start_at)}"
            return video_iframe(
                src,
                "Embedded YouTube video",
                clean_url,
                "Watch on YouTube",
                "video-container" if start_at else "video-embed",
            )
    if "vimeo.com" in host:
        match = re.search(r"/(\d+)", parsed.path)
        if match:
            return video_iframe(
                f"https://player.vimeo.com/video/{html.escape(match.group(1))}",
                "Embedded Vimeo video",
                clean_url,
                "Watch on Vimeo",
            )
    escaped = html.escape(clean_url)
    return f'<p class="media-link"><a href="{escaped}">{escaped}</a></p>'


def video_iframe(src, title, fallback_url, fallback_text, wrapper_class="video-embed"):
    fallback = html.escape(fallback_url)
    return (
        f'<div class="{html.escape(wrapper_class)}">'
        f'<iframe src="{src}" title="{title}" loading="lazy" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
        "allowfullscreen></iframe></div>"
        f'<p class="video-fallback"><a href="{fallback}">{html.escape(fallback_text)}</a></p>'
    )


def shorten_link_text(markup):
    def replace(match):
        href = match.group(1)
        label = html.unescape(match.group(2)).strip()
        if not re.match(r"https?://", label):
            return match.group(0)
        parsed = urlparse(label)
        if "transculturalcollaboration.com" in parsed.netloc:
            text = "Transcultural Collaboration project page"
        elif "landhuman.wordpress.com" in parsed.netloc:
            text = "Project website"
        elif "wordpress.com" in parsed.netloc:
            text = "Exhibition website"
        else:
            text = parsed.netloc.replace("www.", "") or "Open link"
        return f'<a href="{href}">{html.escape(text)}</a>'

    return re.sub(r'<a href="([^"]+)">(https?://[^<]+)</a>', replace, markup)


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
    links += [(NAV_LABELS.get(label, label.title()), prefix + f"{label}/index.html") for label in PRIMARY]
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
    if (ROOT / "assets" / "home-cat-moon.jpg").exists():
        home_image = "assets/home-cat-moon.jpg"
    elif (ROOT / "assets" / "home-cat-moon.png").exists():
        home_image = "assets/home-cat-moon.png"
    else:
        home_image = "2024/04/star-edited.jpg"
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
        if image and re.match(r"https?://", image):
            image_src = image
        elif image:
            image_src = f"../{image}"
        else:
            image_src = ""
        image_html = f'<img src="{image_src}" alt="">' if image_src else '<span class="text-cover">TIME<br>ENOUGH</span>'
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
    content = normalize_dates(content)
    if page["slug"] == "publication":
        content = separate_publication_entries(content)
    if page["slug"] == "dreamscaping":
        content = add_dreamscaping_related_publication(content)
    if page["slug"] in VENUE_DETAILS:
        content = add_venue_detail(content, VENUE_DETAILS[page["slug"]])
    if page["slug"] == "time-enough":
        images = (
            '<div class="project-photo-grid is-large">'
            '<figure><img src="../assets/time-enough-installation-1.png" alt="TIME ENOUGH installation view with projected climate future video and sculptural tubes"></figure>'
            '<figure><img src="../assets/time-enough-installation-2.png" alt="TIME ENOUGH exhibition view with two video screens and installation objects"></figure>'
            "</div>"
        )
        content = content.replace(images, "")
        content = re.sub(
            r'(<p class="video-fallback">[\s\S]*?</p>)(\s*</div>\s*</div>\s*</div>)',
            lambda match: match.group(1) + match.group(2) + images,
            content,
            count=1,
        )
    if page["slug"] in {"dreamscaping", "dreamscapes"}:
        content = move_video_under_first_image(content)
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


def normalize_dates(content):
    content = content.replace("<strong>2026/0</strong>6", "<strong>2026/06</strong>")
    content = re.sub(r"\b(20\d{2})-\1\b", r"\1", content)
    content = re.sub(r"\b([A-Z][a-z]{2}) (20\d{2})-\1 \2\b", r"\1 \2", content)
    content = re.sub(r"\b(20\d{2}) ([A-Z][a-z]+) to \1 \2\b", r"\1 \2", content)
    content = re.sub(r"\b([A-Z][a-z]+) (20\d{2}) to \1 \2\b", r"\1 \2", content)
    return content


def separate_publication_entries(content):
    content = content.replace(
        '</div>\n\n\n\n<div class="wp-block-group">\n<div class="wp-block-group">\n<p class="has-small-font-size"><strong><a href="https://isea-archives.siggraph.org/wp-content/uploads/2025/01/2024_Liu_Falling_Echoes_Expressing_the_Act_of_Falling.pdf">Falling Echoes',
        '</div>\n</div>\n\n\n\n<div class="wp-block-group">\n<div class="wp-block-group">\n<p class="has-small-font-size"><strong><a href="https://isea-archives.siggraph.org/wp-content/uploads/2025/01/2024_Liu_Falling_Echoes_Expressing_the_Act_of_Falling.pdf">Falling Echoes',
        1,
    )
    return content.replace(
        '</div>\n</div>\n</div>\n\n\n\n<div class="wp-block-group">\n<div class="wp-block-group">\n<p class="has-small-font-size"><strong><a href="https://doi.org/10.1145/3613905.3644054">Virtual Dream Reliving',
        '</div>\n</div>\n\n\n\n<div class="wp-block-group">\n<div class="wp-block-group">\n<p class="has-small-font-size"><strong><a href="https://doi.org/10.1145/3613905.3644054">Virtual Dream Reliving',
        1,
    )


def add_dreamscaping_related_publication(content):
    if "10.1145/3803784.3807563" in content:
        return content
    related = (
        '<p class="has-small-font-size"><strong>Related Publication:</strong> '
        '<a href="https://doi.org/10.1145/3803784.3807563">"Illustration of the subconscious mind": '
        'Reinterpreting Dream Material as Artistic Creative Workflows Supported by Generative AI</a></p>'
    )
    return re.sub(
        r'(<p class="has-small-font-size"><strong>Exhibition Website:</strong>[\s\S]*?</p>)',
        lambda match: match.group(1) + "\n\n\n\n" + related,
        content,
        count=1,
    )


def add_venue_detail(content, venue):
    pattern = r'(<p class="has-small-font-size"><strong>[^<]+</strong>(?:, <strong>[^<]+</strong>)?</p>)'
    if venue in content:
        return content
    venue_html = f'<p class="has-small-font-size">{html.escape(venue)}</p>'
    return re.sub(pattern, lambda match: match.group(1) + "\n\n" + venue_html, content, count=1)


def move_video_under_first_image(content):
    video_match = re.search(r'<div class="video-embed">[\s\S]*?<p class="video-fallback">[\s\S]*?</p>', content)
    image_match = re.search(r'(<figure class="wp-block-image[^>]*><img [\s\S]*?</figure>)', content)
    if not video_match or not image_match:
        return content
    video = video_match.group(0)
    content = content[: video_match.start()] + content[video_match.end() :]
    image_match = re.search(r'(<figure class="wp-block-image[^>]*><img [\s\S]*?</figure>)', content)
    return content[: image_match.end()] + video + content[image_match.end() :]


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
