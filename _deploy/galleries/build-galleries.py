#!/usr/bin/env python3
"""Build every page under /galleries/ from one manifest.

    python _deploy/galleries/build-galleries.py --bootstrap   # one-off: read the live pages into manifest.json
    python _deploy/galleries/build-galleries.py               # render all gallery pages, the index,
                                                              # the homepage block and the sitemap entries

manifest.json is the single source of truth: categories (in display order) and
galleries (in display order within a category), each with its photos. Image files
live in galleries/img/<slug>/<slug>-NN.jpg (1600px long edge) + -sm.jpg (800px);
their provenance is in galleries/credits.json.
"""
import html, json, re, sys, unicodedata
from PIL import Image
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAL = ROOT / "galleries"
MANIFEST = Path(__file__).with_name("manifest.json")
SITE = "https://tapephoto.com"
CSS_V = "20261124"
TODAY = date.today().isoformat()
PERSON = {"@type": "Person", "@id": f"{SITE}/#carlos", "name": "Carlos Martinez", "url": f"{SITE}/"}
LICENSE_PAGE = f"{SITE}/licensing.html"

esc = lambda s: html.escape(s, quote=True)

# Spanish copy for every gallery page lives in es.json; each page carries both languages and
# gallery-lang.js shows one (browser language, Spanish referrer, or the visitor's ES / EN toggle).
ES = json.loads(Path(__file__).with_name("es.json").read_text(encoding="utf-8"))


def bi(en, es):
    """Both languages inline; CSS (.bi) hides the one that does not match <html lang>."""
    return f'<span class="bi" lang="en">{en}</span><span class="bi" lang="es">{es}</span>'


def bia(en_attrs, en_text, es_attrs, es_text, cls=""):
    """Two sibling anchors, one per language (hrefs differ: services.html / servicios.html)."""
    c = (cls + " " if cls else "") + "bi"
    return f'<a class="{c}" lang="en" {en_attrs}>{en_text}</a><a class="{c}" lang="es" {es_attrs}>{es_text}</a>'


def es_gallery(g):
    e = ES["galleries"][g["slug"]]
    return dict(title=e["title"], kicker=e["kicker"], intro=e["intro"], label=ES["labels"][g["label"]])


def kicker_es(g, n):
    x = es_gallery(g)
    return " · ".join([x["label"]] + ([x["kicker"]] if x["kicker"] else []) + [f"{n} fotos"])

# Galleries whose CTA also offers a print request (matches the published pages).
PRINT_GALLERIES = frozenset({"andes-glaciers", "coast-travel-wildlife"})
CTA_PRINT = '            <a class="gallery-btn gallery-btn-ghost" href="../prints.html#frames">Request a print</a>\n'


# --------------------------------------------------------------------------- bootstrap
def bootstrap():
    idx = (GAL / "index.html").read_text(encoding="utf-8")
    cats = []
    for m in re.finditer(r'<section class="gallery-section" id="([^"]+)">\s*<div class="gallery-section-head">\s*'
                         r'<h2>(.*?)</h2>\s*<p>(.*?) · \d+ photos</p>(.*?)</section>', idx, re.S):
        cid, name, blurb, body = m.groups()
        slugs = re.findall(r'<a class="gallery-card" href="([^"]+)\.html">', body)
        covers = dict(re.findall(r'<a class="gallery-card" href="([^"]+)\.html">\s*<img src="img/[^/]+/[^"]+-(\d+)-sm\.jpg"', body))
        cats.append(dict(id=cid, name=html.unescape(name), short=html.unescape(name).split(" &")[0].split(" & ")[0].lower(),
                         blurb=html.unescape(blurb), galleries=slugs, covers=covers))
    galleries = []
    for c in cats:
        for slug in c["galleries"]:
            page = (GAL / f"{slug}.html").read_text(encoding="utf-8")
            title = html.unescape(re.search(r"<h1>(.*?)</h1>", page).group(1))
            kicker = html.unescape(re.search(r'<p class="gallery-kicker">(.*?)</p>', page).group(1))
            kparts = kicker.split(" · ")
            intro = html.unescape(re.search(r'<p class="gallery-intro">(.*?)</p>', page, re.S).group(1))
            fulls = re.findall(r'"contentUrl": "[^"]+/(' + re.escape(slug) + r'-\d+)\.jpg",\s*"width": (\d+),\s*"height": (\d+)', page)
            full = {k: (int(w), int(h)) for k, w, h in fulls}
            photos = []
            for src, alt, w, h in re.findall(r'<img src="img/[^"]+/([^"/]+)-sm\.jpg" data-full="[^"]+" alt="(.*?)" width="(\d+)" height="(\d+)"', page):
                alt = re.sub(r" \(photo \d+ of \d+\)$", "", html.unescape(alt))
                fw, fh = full.get(src) or Image.open(GAL / "img" / slug / f"{src}.jpg").size
                photos.append(dict(file=src, alt=alt, w=fw, h=fh, sw=int(w), sh=int(h)))
            cover = int(c["covers"].get(slug, "1")) - 1
            card_alt = re.search(r'<a class="gallery-card" href="' + re.escape(slug) + r'\.html">\s*<img [^>]*alt="(.*?)"', idx, re.S)
            galleries.append(dict(slug=slug, title=title, category=c["id"], label=kparts[0],
                                  kicker=" · ".join(kparts[1:-1]), intro=intro, cover=cover,
                                  cover_alt=html.unescape(card_alt.group(1)) if card_alt else photos[cover]["alt"],
                                  updated="2026-10-02", photos=photos))
    for c in cats:
        c.pop("galleries"); c.pop("covers")
    intro = html.unescape(re.search(r'<p class="gallery-intro">(.*?)</p>', idx, re.S).group(1))
    MANIFEST.write_text(json.dumps(dict(intro=intro, categories=cats, galleries=galleries), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"bootstrapped {len(galleries)} galleries, {sum(len(g['photos']) for g in galleries)} photos")


# --------------------------------------------------------------------------- shared chrome
WA_EN = "https://wa.me/14423854585?text=Hi%2C%20I%20found%20tapephoto.com%20and%20want%20a%20quote%20for%20a%20photo%20shoot"
WA_ES = "https://wa.me/14423854585?text=Hola%2C%20encontr%C3%A9%20tapephoto.com%20y%20quiero%20cotizar%20una%20sesi%C3%B3n%20de%20fotos"
WA_ATTRS = 'target="_blank" rel="noopener"'

# (English href, English text, Spanish href, Spanish text)
NAV = [("/en/#work", "Work", "/#work", "Portafolio"),
       ("../galleries/", "Galleries", "../galleries/", "Galer&iacute;as"),
       ("../services.html", "Services", "../servicios.html", "Servicios"),
       ("../licensing.html", "Licensing", "../licencias.html", "Licencias"),
       ("../blog/", "Blog", "../blog/", "Blog"),
       ("../prints.html", "Prints", "../impresiones.html", "Impresiones"),
       ("../about.html", "About", "../sobre-mi.html", "Sobre m&iacute;"),
       ("../contact.html", "Contact", "../contacto.html", "Contacto")]
FOOT_NAV = NAV + [("../privacy.html", "Privacy", "../privacidad.html", "Privacidad"),
                  ("../terms.html", "Terms", "../terminos.html", "T&eacute;rminos")]


def links(items, indent):
    return "".join(f"{indent}{bia(f'href={chr(34)}{eh}{chr(34)}', et, f'href={chr(34)}{sh}{chr(34)}', st)}\n" for eh, et, sh, st in items)


LOGO = bia('href="/en/"', "tapephoto", 'href="/"', "tapephoto", "logo")

HEADER = f"""    <header class="header">
        {LOGO}
        <button class="menu-toggle" aria-label="Menu / Men&uacute;" aria-expanded="false" aria-controls="site-nav">
            <span></span><span></span>
        </button>
        <nav class="nav" id="site-nav">
{links(NAV, "            ")}        </nav>
    </header>
"""

CTA = f"""        <section class="gallery-cta">
            <h2>{bi("Need coverage like this?", "&iquest;Necesitas una cobertura como esta?")}</h2>
            <p>{bi('Motorsport, events, aerials and commercial work &mdash; in Chile and abroad. Archive images available for <a href="../licensing.html">licensing</a>.', 'Automovilismo, eventos, tomas a&eacute;reas y trabajo comercial &mdash; en Chile y en el extranjero. Im&aacute;genes del archivo disponibles para <a href="../licencias.html">licenciar</a>.')}</p>
            @@LICENSE@@            {bia('href="../contact.html"', "Get in touch", 'href="../contacto.html"', "Escr&iacute;beme", "gallery-btn gallery-btn-ghost")}
            {bia(f'href="{WA_EN}" {WA_ATTRS}', "WhatsApp", f'href="{WA_ES}" {WA_ATTRS}', "WhatsApp", "gallery-btn gallery-btn-ghost")}
        </section>
""".replace("&mdash;", "—").replace("%", "%%").replace("@@LICENSE@@", "%(license)s")
CTA_LICENSE = (bia('href="../licensing.html?ref=%s#inquiry"', "License this event", 'href="../licencias.html?ref=%s#inquiry"', "Licenciar este evento", "gallery-btn") + "\n").replace("%s", "%(slug)s")
CTA_PLAIN = bia('href="../prints.html"', "Prints from the archive", 'href="../impresiones.html"', "Impresiones del archivo", "gallery-btn") + "\n"

FOOTER = f"""    <footer class="footer">
        <div class="footer-inner">
            <div class="footer-brand">
                {LOGO}
                <p>Carlos Martinez Photography<br>Coquimbo, Chile</p>
                <div class="footer-contact">
                    <a href="mailto:carlos@netwebmedia.com">carlos@netwebmedia.com</a>
                    {bia(f'href="{WA_EN}" {WA_ATTRS}', "WhatsApp +1 (442) 385-4585", f'href="{WA_ES}" {WA_ATTRS}', "WhatsApp +1 (442) 385-4585")}
                </div>
            </div>
            <div class="footer-links">
                <h3>{bi("Navigate", "Navegar")}</h3>
{links(FOOT_NAV, "                ")}            </div>
            <div class="footer-social">
                <h3>{bi("Follow", "Sigue")}</h3>
                <a href="https://www.instagram.com/tapephotocom/" target="_blank" rel="me noopener">Instagram &mdash; @tapephotocom</a>
                <a href="https://www.facebook.com/tapephoto" target="_blank" rel="me noopener">Facebook</a>
            </div>
        </div>
        <div class="footer-bottom">
            <p>{bi('&copy; 2026 TapePhoto &mdash; all photographs by Carlos Martinez. All rights reserved. <a href="../licensing.html">Licensing</a>', '&copy; 2026 TapePhoto &mdash; todas las fotograf&iacute;as son de Carlos Martinez. Todos los derechos reservados. <a href="../licencias.html">Licencias</a>')}</p>
            <p>{bi('A <a href="https://dongaston.com/" rel="noopener">Don Gast&oacute;n</a> company', 'Una empresa de <a href="https://dongaston.com/" rel="noopener">Don Gast&oacute;n</a>')}</p>
        </div>
    <div class="nwm-credit">{bi('Made by <a href="https://netwebmedia.com/?utm_source=tapephoto&amp;utm_medium=footer&amp;utm_campaign=made-by" rel="noopener">NetWebMedia</a> · est. 2006 · <a class="nwm-credit-cta" href="https://netwebmedia.com/free-audit.html?utm_source=tapephoto&amp;utm_medium=footer&amp;utm_campaign=made-by" rel="noopener">Want a site like this? Get a free audit &rarr;</a>', 'Hecho por <a href="https://netwebmedia.com/?utm_source=tapephoto&amp;utm_medium=footer&amp;utm_campaign=made-by" rel="noopener">NetWebMedia</a> · desde 2006 · <a class="nwm-credit-cta" href="https://netwebmedia.com/free-audit.html?utm_source=tapephoto&amp;utm_medium=footer&amp;utm_campaign=made-by" rel="noopener">&iquest;Quieres un sitio como este? Pide una auditor&iacute;a gratis</a>')}</div>
    </footer>
"""

LANGBAR = f"""            <div class="gallery-langbar">
                <div class="lang-toggle" role="group" aria-label="Idioma / Language">
                    <button type="button" class="lang-btn" data-lang-set="es" lang="es" aria-pressed="false">ES</button>
                    <button type="button" class="lang-btn" data-lang-set="en" lang="en" aria-pressed="false">EN</button>
                </div>
                <p class="gallery-es">{bia('href="/en/"', "&larr; Back to TapePhoto", 'href="/"', "&larr; Volver a TapePhoto")}</p>
            </div>
"""


def head(title, desc, canonical, og_img, og_w, og_h, ld, title_es):
    return f"""<!DOCTYPE html>
<html lang="en" data-title-es="{esc(title_es)}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(desc)}">
    <link rel="canonical" href="{canonical}">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="TapePhoto">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{og_img}">
    <meta property="og:image:width" content="{og_w}">
    <meta property="og:image:height" content="{og_h}">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="icon" href="/favicon.ico" sizes="32x32">
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <link rel="preload" href="/fonts/inter-300-700.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="/fonts/playfair-display-400-700.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="stylesheet" href="../style.css?v={CSS_V}">
    <script src="../gallery-lang.js?v={CSS_V}"></script>
    <script type="application/ld+json">
{json.dumps(ld, indent=2, ensure_ascii=False)}
    </script>
    <link rel="preconnect" href="https://www.googletagmanager.com">
    <script src="../analytics.js?v=3" defer></script>
</head>
"""


def clip(text, n):
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0].rstrip(",;:—-– ") + "…"


def img_url(g, p, sm=False):
    return f"img/{g['slug']}/{p['file']}{'-sm' if sm else ''}.jpg"


# --------------------------------------------------------------------------- pages
def gallery_page(g, cat, order):
    n = len(g["photos"])
    url = f"{SITE}/galleries/{g['slug']}.html"
    cover = g["photos"][g["cover"]]
    title = f"{g['title']} | TapePhoto Galleries"
    desc = clip(f"{g['title']} — {n} photographs by Carlos Martinez (TapePhoto). {g['intro']}", 170)
    images = []
    for i, p in enumerate(g["photos"], 1):
        images.append({"@type": "ImageObject", "contentUrl": f"{SITE}/galleries/{img_url(g, p)}",
                       "width": p["w"], "height": p["h"], "creator": PERSON,
                       "creditText": "Carlos Martinez / TapePhoto",
                       "copyrightNotice": "© Carlos Martinez — TapePhoto",
                       "name": f"{g['title']}, photo {i}", "caption": p["alt"],
                       "thumbnailUrl": f"{SITE}/galleries/{img_url(g, p, True)}",
                       "encodingFormat": "image/jpeg",
                       "license": LICENSE_PAGE, "acquireLicensePage": f"{LICENSE_PAGE}#inquiry"})
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "ImageGallery", "@id": f"{url}#gallery", "name": g["title"], "description": g["intro"], "url": url,
         "author": PERSON, "creator": PERSON, "copyrightHolder": PERSON, "numberOfItems": n,
         "genre": cat["name"], "dateModified": g["updated"], "image": images},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Galleries", "item": f"{SITE}/galleries/"},
            {"@type": "ListItem", "position": 3, "name": cat["name"], "item": f"{SITE}/galleries/#{cat['id']}"},
            {"@type": "ListItem", "position": 4, "name": g["title"], "item": url}]}]}
    kicker = " · ".join([g["label"]] + ([g["kicker"]] if g["kicker"] else []) + [f"{n} photos"])
    x = es_gallery(g)
    cat_es = ES["categories"][cat["id"]]
    out = [head(title, desc, url, f"{SITE}/galleries/{img_url(g, cover)}", cover["w"], cover["h"], ld,
                f"{x['title']} | Galer\u00edas TapePhoto")]
    out.append('<body class="gallery-body">\n' + HEADER + '\n    <main class="gallery-page">\n')
    out.append(f"""        <section class="gallery-hero">
""" + LANGBAR + f"""            <nav class="gallery-crumbs" aria-label="Breadcrumb">{bia('href="/en/"', "Home", 'href="/"', "Inicio")} / {bia('href="./"', "Galleries", 'href="./"', "Galer&iacute;as")} / {bia(f'href="./#{cat["id"]}"', esc(cat['name']), f'href="./#{cat["id"]}"', esc(cat_es['name']))} / <span>{bi(esc(g['title']), esc(x['title']))}</span></nav>
            <p class="gallery-kicker">{bi(esc(kicker), esc(kicker_es(g, n)))}</p>
            <h1>{bi(esc(g['title']), esc(x['title']))}</h1>
            <p class="gallery-intro">{bi(esc(g['intro']), esc(x['intro']))}</p>
        </section>

        <section class="gallery-masonry" aria-label="{esc(g['title'])} photographs" data-aria-es="Fotograf&iacute;as: {esc(x['title'])}">
""")
    for i, p in enumerate(g["photos"], 1):
        out.append(f"""            <figure class="photo-item gallery-item" tabindex="0" role="button" aria-label="Open photo {i} of {n} full size" data-aria-es="Abrir foto {i} de {n} en tama&ntilde;o completo">
                <img src="{img_url(g, p, True)}" data-full="{img_url(g, p)}" alt="{esc(p['alt'])} (photo {i} of {n})" width="{p['sw']}" height="{p['sh']}" loading="{'eager' if i <= 3 else 'lazy'}" decoding="async">
            </figure>
""")
    out.append("        </section>\n\n" + CTA % {"license": CTA_LICENSE % {"slug": g["slug"]} + (CTA_PRINT if g["slug"] in PRINT_GALLERIES else "")} + f"""
        <section class="gallery-more">
            <h2>{bi("More galleries", "M&aacute;s galer&iacute;as")}</h2>
            <div class="gallery-more-links">
""")
    for o in order:
        if o["slug"] != g["slug"]:
            out.append("                " + bia(f'href="{o["slug"]}.html"', esc(o["title"]), f'href="{o["slug"]}.html"', esc(ES["galleries"][o["slug"]]["title"])) + "\n")
    out.append("""            </div>
        </section>
    </main>

""" + FOOTER + f"""
    <div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Photo viewer" data-aria-es="Visor de fotos">
        <button class="lightbox-close" aria-label="Close" data-aria-es="Cerrar">&times;</button>
        <button class="lightbox-prev" aria-label="Previous" data-aria-es="Anterior">&lsaquo;</button>
        <button class="lightbox-next" aria-label="Next" data-aria-es="Siguiente">&rsaquo;</button>
        <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" alt="" class="lightbox-img">
        <a class="lightbox-license" href="../licensing.html#inquiry">{bi("License this photo", "Licenciar esta foto")}</a>
    </div>

    <script src="../main.js" defer></script>
</body>
</html>
""")
    return "".join(out)


def card(g, prefix, label, count_text, eager, keywords=False):
    p = g["photos"][g["cover"]]
    kw = ""
    if keywords:
        meta = " · ".join([g["label"]] + ([g["kicker"]] if g["kicker"] else []) + [f"{len(g['photos'])} photos"])
        x = es_gallery(g)
        words = " ".join([g["title"], g["label"], g["cover_alt"], meta, g["intro"], x["title"], x["label"], x["kicker"], x["intro"]]).lower()
        # accent-stripped copy too, so "aereas" finds "a\u00e9reas" (main.js strips accents from the query)
        words += " " + "".join(ch for ch in unicodedata.normalize("NFD", words) if unicodedata.category(ch) != "Mn")
        kw = f' data-keywords="{esc(words)}"'
    return f"""            <a class="gallery-card" href="{prefix}{g['slug']}.html"{kw}>
                <img src="{prefix}{img_url(g, p, True)}" alt="{esc(g['cover_alt'])}" width="{p['sw']}" height="{p['sh']}" loading="{'eager' if eager else 'lazy'}" decoding="async">
                <span class="gallery-card-body">
                    <span class="photo-category">{bi(esc(label), esc(es_gallery(g)['label']))}</span>
                    <span class="gallery-card-title">{bi(esc(g['title']), esc(es_gallery(g)['title']))}</span>
                    <span class="gallery-card-count">{bi(count_text, count_text.replace(" photos", " fotos").replace(" photo", " foto"))}</span>
                </span>
            </a>
"""


def index_page(M, order, by_cat):
    total = sum(len(g["photos"]) for g in order)
    ncat = len(by_cat)
    names = ", ".join(c["name"].lower() for c in M["categories"])
    desc = f"{total} curated photographs by Carlos Martinez in {len(order)} galleries across {names}."
    first = order[0]
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": f"{SITE}/galleries/#page",
          "name": "Photo Galleries — TapePhoto", "url": f"{SITE}/galleries/", "author": PERSON,
          "dateModified": max(g["updated"] for g in order),
          "hasPart": [{"@type": "ImageGallery", "name": g["title"], "genre": c["name"],
                       "url": f"{SITE}/galleries/{g['slug']}.html", "numberOfItems": len(g["photos"])}
                      for c in M["categories"] for g in by_cat[c["id"]]]}
    out = [head("Photo Galleries | TapePhoto - Carlos Martinez Photography", desc, f"{SITE}/galleries/",
                f"{SITE}/galleries/{img_url(first, first['photos'][first['cover']])}",
                first["photos"][first["cover"]]["w"], first["photos"][first["cover"]]["h"], ld, ES["index_title"])]
    jump = " ".join(f'<a href="#{c["id"]}">{bi(esc(c["name"]), esc(ES["categories"][c["id"]]["name"]))}</a>' for c in M["categories"])
    out.append('<body class="gallery-body">\n' + HEADER + f"""
    <main class="gallery-page">
        <section class="gallery-hero">
""" + LANGBAR + f"""            <nav class="gallery-crumbs" aria-label="Breadcrumb">{bia('href="/en/"', "Home", 'href="/"', "Inicio")} / <span>{bi("Galleries", "Galer&iacute;as")}</span></nav>
            <p class="gallery-kicker">{bi(f"{total} photographs · {len(order)} galleries · {ncat} categories", f"{total} fotograf&iacute;as · {len(order)} galer&iacute;as · {ncat} categor&iacute;as")}</p>
            <h1>{bi("Galleries", "Galer&iacute;as")}</h1>
            <p class="gallery-intro">{bi(esc(M['intro']), esc(ES['intro']))}</p>
            <nav class="gallery-jump" aria-label="Categories" data-aria-es="Categor&iacute;as">{jump}</nav>
        </section>

        <div class="gallery-search" role="search">
            <label for="gallery-search">{bi("Search the archive", "Buscar en el archivo")}</label>
            <input id="gallery-search" type="search" placeholder="Event, place or subject: rally, Tijuana, aerial, portrait..." data-placeholder-es="Evento, lugar o tema: rally, Tijuana, a&eacute;reas, retrato..." autocomplete="off">
            <p id="gallery-search-status" class="gallery-search-status" role="status" aria-live="polite"></p>
        </div>
""")
    first_card = True
    for c in M["categories"]:
        gs = by_cat[c["id"]]
        cnt = sum(len(g["photos"]) for g in gs)
        out.append(f"""
        <section class="gallery-section" id="{c['id']}">
            <div class="gallery-section-head">
                <h2>{bi(esc(c['name']), esc(ES['categories'][c['id']]['name']))}</h2>
                <p>{bi(esc(c['blurb']) + f" · {cnt} photos", esc(ES['categories'][c['id']]['blurb']) + f" · {cnt} fotos")}</p>
            </div>
            <div class="gallery-cards">
""")
        for g in gs:
            out.append(card(g, "", g["label"], f"{len(g['photos'])} photos", first_card, keywords=True))
            first_card = False
        out.append("            </div>\n        </section>")
    out.append("\n\n" + CTA % {"license": CTA_PLAIN} + "    </main>\n\n" + FOOTER + """
    <script src="../main.js" defer></script>
</body>
</html>
""")
    return "".join(out)


def home_picks(gs, n=3):
    # Up to n homepage thumbnails per category: each gallery's cover first, then
    # evenly spaced frames from the category's remaining photos.
    picks = [(g, g["photos"][g["cover"]]) for g in gs][:n]
    rest = [(g, ph) for g in gs for ph in g["photos"] if all(ph is not q for _, q in picks)]
    need = min(n - len(picks), len(rest))
    step = len(rest) / need if need > 0 else 0
    return picks + [rest[int(i * step + step / 2)] for i in range(max(need, 0))]


def home_block(M, order, by_cat):
    # The homepage's archive section (the scroll-craft darkroom page): real counts
    # that tick up on entry, then the category index. Markup must match index.html.
    total = sum(len(g["photos"]) for g in order)
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    cats = []
    for c in M["categories"]:
        gs = by_cat[c["id"]]
        cnt = sum(len(x["photos"]) for x in gs)
        # Joni r3: the first thumbnail loads eagerly (nothing blank in a full-page capture); the page shows one per category.
        thumbs = "".join(f'<img src="galleries/{img_url(g, ph, sm=True)}" width="{ph["sw"]}" height="{ph["sh"]}" alt="" {"" if k == 0 else "loading=" + chr(34) + "lazy" + chr(34) + " "}decoding="async">'
                         for k, (g, ph) in enumerate(home_picks(gs)))
        cats.append(f'                <li><a href="galleries/#{c["id"]}"><span class="c">{esc(c["name"])}</span>'
                    f'<span class="k">{plural(cnt, "photograph")} · {plural(len(gs), "gallery").replace("gallerys", "galleries")}</span>'
                    f'<span class="t">{thumbs}</span></a></li>\n')
    return f"""    <!-- Galleries: the archive in its real numbers (rebuilt by _deploy/galleries/build-galleries.py) -->
    <section id="galleries" class="archive">
        <div class="sc-wrap">
            <div class="archive__head">
                <h2>The archive</h2>
            </div>
            <div class="archive__nums">
                <p><b>{total}</b>photographs</p>
                <p><b>{len(order)}</b>galleries</p>
                <p><b>{len(M['categories'])}</b>categories</p>
            </div>
            <ul class="archive__cats">
{''.join(cats)}            </ul>
            <p class="archive__links"><a class="btn" href="galleries/">All galleries</a> <a class="btn" href="licensing.html">How licensing works</a> <a class="btn" href="prints.html">Prints</a></p>
        </div>
    </section>
"""


def sitemap(order):
    sm = ROOT / "sitemap.xml"
    s = sm.read_text(encoding="utf-8")
    s = re.sub(r"\s*<url>\s*<loc>https://tapephoto\.com/galleries/[^<]+\.html</loc>.*?</url>", "", s, flags=re.S)
    block = "".join(f"""
  <url>
    <loc>{SITE}/galleries/{g['slug']}.html</loc>
    <lastmod>{g['updated']}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>""" for g in order)
    s = re.sub(r"(<url>\s*<loc>https://tapephoto\.com/galleries/</loc>\s*<lastmod>)[^<]*(</lastmod>.*?</url>)",
               lambda m: m.group(1) + max(g["updated"] for g in order) + m.group(2) + block, s, count=1, flags=re.S)
    sm.write_text(s, encoding="utf-8")


def build():
    M = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cats = {c["id"]: c for c in M["categories"]}
    by_cat = {c["id"]: [g for g in M["galleries"] if g["category"] == c["id"]] for c in M["categories"]}
    order = [g for c in M["categories"] for g in by_cat[c["id"]]]
    for g in order:
        for p in g["photos"]:
            for suffix in ("", "-sm"):
                f = GAL / "img" / g["slug"] / f"{p['file']}{suffix}.jpg"
                if not f.is_file():
                    sys.exit(f"missing image {f}")
        (GAL / f"{g['slug']}.html").write_text(gallery_page(g, cats[g["category"]], order), encoding="utf-8", newline="\n")
    (GAL / "index.html").write_text(index_page(M, order, by_cat), encoding="utf-8", newline="\n")
    # The homepages (index.html in Spanish, en/index.html in English) are hand-authored twins with
    # their own alt text, so this script no longer rewrites their archive block. Update the counts
    # in both pages by hand when the galleries change.
    sitemap(order)
    print(f"built {len(order)} galleries, {sum(len(g['photos']) for g in order)} photos, {len(M['categories'])} categories")


if __name__ == "__main__":
    bootstrap() if "--bootstrap" in sys.argv else build()
