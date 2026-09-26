"""Daily trend blog generator. Usage: python scripts/daily_trend_blog.py (exit 1 on failure).

Fetches Google Daily Search Trends (India RSS), picks the most business-relevant
trend, and publishes a validator-compliant blog post: new blog-*.html + card in
blog.html + URL in sitemap.xml + line in llms.txt. If no trend is business
relevant (cricket, weather, lottery, ...), falls back to an evergreen marketing
topic so every auto-post stays on-topic for Brand U Max. One post per day max.
Only stdlib is used so GitHub Actions needs no extra installs.
"""
import datetime
import html
import json
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRENDS_URL = "https://trends.google.co.in/trending/rss?geo=IN"
GBP_URL = "https://www.google.com/maps/place/BrandUMax/@11.0453001,76.9488225,17z/data=!3m1!4b1!4m6!3m5!1s0x3ba859e1c1217937:0x140e0b0fa270d76f!8m2!3d11.0453001!4d76.9488225!16s%2Fg%2F11nvgvz3d7?entry=ttu"
PHONE_TEL = "+919941913167"
PHONE_DISP = "+91 9941913167"
WA_LINK = "https://wa.me/919941913167?text=Hi%20Brand%20U%20Max%2C%20I%20want%20a%20free%20audit"

RELEVANT = ("market", "advertis", "seo", "google", "instagram", "youtube",
            "facebook", "meta", " ai", "gpt", "openai", "gemini", "artificial",
            "startup", "business", "ecommerce", "e-commerce", "online shopping",
            "amazon", "flipkart", "brand", "digital", "social media", "whatsapp",
            "iphone", "smartphone", "android", "price", "sale", "offer", "phone",
            "laptop", "election", "budget", "gst", "stock", "ipo", "festival",
            "diwali", "pongal", "cricket world", "ipl")
SKIP = ("weather", "mausam", "kal ka", "lottery", "sangbad", "sambad", "horoscope",
        "rashifal", "mandi bhav", "gold rate today", "petrol price")

EVERGREEN = [
    ("free-google-business-audit", "Why Every Coimbatore Business Needs a Free Google Business Audit",
     "A 10-minute audit finds the category, keyword and review gaps costing you Maps calls.",
     ("Check your primary category against what buyers search.",
      "Compare your services list with RS Puram and Peelamedu demand.",
      "Count reviews in the last 90 days and reply gaps.")),
    ("instagram-reels-reach", "Instagram Reels Reach in Tamil Nadu: What Small Budgets Win",
     "Short video is the cheapest reach in 2026; consistency beats production value.",
     ("Post 3 reels a week answering one buyer question each.",
      "Repurpose every reel to Shorts, Facebook and WhatsApp Status.",
      "Track profile visits and WhatsApp clicks, not just views.")),
    ("google-reviews-velocity", "Google Review Velocity: The 18-Day Rule for Coimbatore Maps",
     "Rankings slip when no new review arrives for 3 weeks; velocity beats total count.",
     ("Ask every customer, never gate or filter reviews.",
      "Request service plus area wording in the review.",
      "Reply within 1-3 days with specifics, not generic thanks.")),
    ("meta-ads-vs-google-ads", "Meta Ads vs Google Ads for Coimbatore Local Businesses",
     "Google catches ready buyers; Meta creates demand. Most local budgets need both.",
     ("Run search ads on high-intent service plus city terms.",
      "Run Meta reels ads to RS Puram and Peelamedu audiences.",
      "Send both to WhatsApp or a fast call page, then track cost per lead.")),
    ("local-keywords-rs-puram", "How RS Puram and Peelamedu Buyers Search (and How to Rank)",
     "Neighborhood modifiers convert better than city terms and are easier to win.",
     ("Add one service entry per area you serve.",
      "Geo-tag photos in RS Puram, Peelamedu and Gandhipuram.",
      "Collect reviews naming the service and the area.")),
    ("whatsapp-lead-machine", "Turn WhatsApp Into Your Lead Machine in Tamil Nadu",
     "Click-to-chat beats forms for local buyers; speed of reply decides the sale.",
     ("Put click-to-WhatsApp above the fold on mobile.",
      "Auto-reply instantly, follow up within 5 minutes.",
      "Catalogue your services so chats convert without calls.")),
    ("festival-marketing-tamilnadu", "Festival Marketing Calendar for Tamil Nadu Businesses",
     "Diwali, Pongal and wedding season spikes reward businesses that plan content early.",
     ("Plan festive reels and offers 3-4 weeks ahead.",
      "Refresh GBP photos and posts for each festival.",
      "Retarget festive visitors with Meta ads after the spike.")),
    ("seo-vs-ads-budget", "SEO vs Ads: Where Should a Coimbatore Budget Go First",
     "Ads buy this month, SEO buys every month after. Sequence them right.",
     ("Start ads for instant leads while SEO builds.",
      "Publish one service plus area page per month.",
      "Shift budget to SEO as organic cost per lead drops.")),
    ("branding-before-ads", "Why Branding Must Come Before Ad Spend",
     "Ads amplify identity; a forgettable brand just buys expensive clicks.",
     ("Fix logo, colors and voice before scaling spend.",
      "Keep one look across GBP, Instagram and website.",
      "Measure branded searches rising as proof.")),
    ("youtube-shorts-discovery", "YouTube Shorts: Coimbatore Buyers Discover You There First",
     "Search-driven Shorts keep working months after posting, unlike feed posts.",
     ("Answer one how-to question per Short with the keyword spoken aloud.",
      "Link every Short to WhatsApp or your location page.",
      "Repost winners as Instagram reels.")),
    ("nap-consistency", "NAP Consistency: The Boring Fix That Lifts Maps Rankings",
     "Mismatched name, address or phone across directories silently drains relevance.",
     ("Match GBP, footer, schema and WhatsApp digit for digit.",
      "Fix Justdial, IndiaMART, Sulekha, Bing Places and Apple Maps.",
      "Recheck quarterly; aggregators revert edits silently.")),
    ("linkedin-b2b-coimbatore", "LinkedIn B2B Leads for Coimbatore Manufacturers and Services",
     "Decision-makers in SIDCO estates and hospitals live on LinkedIn, not Instagram.",
     ("Publish one proof post weekly: result, process, client quote.",
      "Run sponsored content to Coimbatore job titles.",
      "Route replies to a call page, not a cold form.")),
]


def fetch_trends():
    req = urllib.request.Request(TRENDS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as res:
        data = res.read()
    ns = {"ht": "https://trends.google.com/trending/rss"}
    items = []
    for it in ET.fromstring(data).findall("./channel/item"):
        title = (it.findtext("title") or "").strip()
        traffic = (it.findtext("ht:approx_traffic", namespaces=ns) or "0+").strip()
        news = [ (n.findtext("ht:news_item_title", namespaces=ns) or "").strip()
                 for n in it.findall("ht:news_item", ns)][:3]
        news = [n for n in news if n]
        try:
            num = int(re.sub(r"\D", "", traffic) or 0)
        except ValueError:
            num = 0
        if title:
            items.append({"title": title, "traffic": traffic, "num": num, "news": news})
    return items


def pick_trend(items):
    scored = []
    for it in items:
        low = it["title"].lower()
        if len(low.strip()) < 3:
            continue
        if any(s in low for s in SKIP):
            continue
        if any(k in low for k in RELEVANT):
            scored.append(it)
    scored.sort(key=lambda x: x["num"], reverse=True)
    return scored[0] if scored else None


def slugify(text, limit=45):
    s = re.sub(r"[^a-z0-9 ]", "", text.lower())
    s = re.sub(r"\s+", "-", s).strip("-")[:limit].strip("-")
    return s or "trend"


def trend_topic(trend):
    title = trend["title"]
    slug = slugify(title)
    news = trend["news"] or ["Today's top story in India."]
    bullets = news[:3]
    while len(bullets) < 3:
        bullets.append("Follow-up searches spike within hours of the first headlines.")
    headline = f"{title.title()} Is Trending in India: What Businesses Should Do"
    desc = (f"{title.title()} is trending in India ({trend['traffic']} searches). "
            "How Tamil Nadu brands ride the moment.")
    points = tuple(f"{b} Post your brand's take within hours, while search interest peaks."
                   for b in bullets)
    faqs = (
        (f"Why is {title} trending in India?",
         f"{title} is among India's top searches today with {trend['traffic']} "
         "search volume, driven by breaking news coverage."),
        ("How can a small business use a trend like this?",
         "Publish one quick reel or post connecting the trend to your service, "
         "then link it to WhatsApp so attention converts to enquiries."),
        ("Should every trend get a post?",
         "No. Only trends your buyers care about. A Coimbatore retailer gains "
         "nothing from an irrelevant national story."),
    )
    return slug, headline, desc, points, faqs


def meta_desc(text):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= 139 else text[:136].rsplit(" ", 1)[0] + "..."


def build_html(slug, headline, desc, points, faqs, date_h, date_iso):
    esc = html.escape
    faq_json = [{"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]
    bullets = "\n".join(f"<li>{esc(p)}</li>" for p in points)
    faq_vis = "\n".join(
        f'<details class="faq-item">\n<summary>{esc(q)}</summary>\n<p>{esc(a)}</p>\n</details>'
        for q, a in faqs)
    url = f"https://brandumax.com/{slug}.html"
    mdesc = esc(meta_desc(desc))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="X-Content-Type-Options" content="nosniff">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}</script>
<script src="assets/consent.js?v=2"></script>
<title>{esc(headline)} | Brand U Max</title>
<meta name="description" content="{mdesc}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/png" href="assets/logo-feather.png">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Brand U Max">
<meta property="og:title" content="{esc(headline)} | Brand U Max">
<meta property="og:description" content="{mdesc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://brandumax.com/assets/hero-poster.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(headline)} | Brand U Max">
<meta name="twitter:description" content="{mdesc}">
<meta name="twitter:image" content="https://brandumax.com/assets/hero-poster.jpg">
<script type="application/ld+json">
{json.dumps({"@context": "https://schema.org", "@type": "LocalBusiness", "name": "Brand U Max", "url": "https://brandumax.com/", "address": {"@type": "PostalAddress", "streetAddress": "49, Labours Colony, Venkateswara Nagar, Koundampalayam", "addressLocality": "Coimbatore", "addressRegion": "Tamil Nadu", "postalCode": "641030", "addressCountry": "IN"}, "description": meta_desc(desc), "email": "info@brandumax.com", "telephone": PHONE_TEL, "logo": "https://brandumax.com/assets/logo-feather.png", "image": "https://brandumax.com/assets/hero-poster.jpg", "priceRange": "₹₹₹", "geo": {"@type": "GeoCoordinates", "latitude": "11.0453001", "longitude": "76.9488225"}, "openingHours": "Mo-Sa 09:30-18:30", "sameAs": ["https://www.instagram.com/brandumax/", GBP_URL, "https://www.linkedin.com/company/brandumax"]}, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps({"@context": "https://schema.org", "@type": "BlogPosting", "mainEntityOfPage": url, "headline": headline, "description": meta_desc(desc), "datePublished": date_iso, "dateModified": date_iso, "author": {"@type": "Organization", "name": "Brand U Max"}, "publisher": {"@type": "Organization", "name": "Brand U Max", "logo": {"@type": "ImageObject", "url": "https://brandumax.com/assets/logo-feather.png"}}, "image": "https://brandumax.com/assets/hero-poster.jpg"}, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://brandumax.com/"}, {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://brandumax.com/blog.html"}, {"@type": "ListItem", "position": 3, "name": headline, "item": url}]}, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_json}, ensure_ascii=False)}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Lora:ital,wght@0,400;0,500;1,400&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css?v=2">
</head>
<body>

<header class="site-header">
<div class="nav-wrap">
<a href="/" class="brand">
<img class="brand-logo-img" src="assets/logo-feather.png" width="149" height="128" alt="Brand U Max logo">
Brand U Max
</a>
<nav class="nav-links">
<a href="/">Home</a>
<a href="about.html">About Us</a>
<a href="services.html">Services</a>
<a href="blog.html" class="active">Blog</a>
<a href="contact.html">Contact Us</a>
</nav>
<a href="contact.html" class="nav-cta">Get a Free Audit</a>
</div>
</header>

<section class="page-hero">
<div class="eyebrow">Daily Trend &amp; Local Growth</div>
<h1>{esc(headline)}</h1>
<p>{date_h} &middot; 4 min read</p>
</section>

<section class="section">
<div class="container" style="max-width:760px;">
<p><a href="blog.html">&larr; Back to Blog</a></p>

<p>{esc(desc)} Below is the quick, practical take for Coimbatore and Tamil Nadu businesses.</p>

<img src="assets/hero-poster.jpg" width="848" height="478" alt="{esc(headline)}" loading="lazy" style="width:100%;height:auto;border-radius:12px;margin:24px 0;">

<h2>What Happened and Why It Matters</h2>
<ul>
{bullets}
</ul>

<h2>What Coimbatore Businesses Should Do Today</h2>
<p>Attention peaks last hours, not days. Publish one reel or GBP post connecting this to your service, serve RS Puram, Peelamedu and Gandhipuram buyers first, and route every click to WhatsApp or a call page so interest becomes enquiries.</p>

<h2>How Brand U Max Can Help</h2>
<p>At Brand U Max in Koundampalayam, Coimbatore, we turn daily moments into leads with reels, GBP posts and Meta ads. <strong>Build visibility. Build trust. Grow your business.</strong></p>

<p><a href="contact.html" class="btn btn-primary">Get a Free Audit</a> <a href="seo-services.html" class="btn btn-outline">Explore Our SEO Services</a></p>
<p>Related reading: <a href="blog-tamilnadu-high-search-keywords.html">High-Search Keywords in Tamil Nadu</a> and <a href="blog-gbp-ranking-coimbatore.html">Rank Your GBP in Coimbatore</a>.</p>
</div>
</section>

<section class="section section-alt">
<div class="container">
<div class="section-header">
<div class="eyebrow">FAQ</div>
<h2>Frequently Asked Questions</h2>
</div>
<div class="faq-list">
{faq_vis}
</div>
</div>
</section>

<section class="cta-band">
<h2>Want Daily Moments Turned Into Leads?</h2>
<p>Get a free audit and we will map your trend, keyword and GBP plan.</p>
<a href="contact.html" class="btn btn-primary">Get a Free Audit</a>
</section>

<footer class="site-footer">
<div class="footer-inner">
<div class="footer-col">
<h3>Brand U Max</h3>
<p>Helping brands build identity, grow business and scale revenue and profit through branding, business growth and AI marketing.</p>
</div>
<div class="footer-col">
<h3>Quick Links</h3>
<a href="/">Home</a>
<a href="about.html">About Us</a>
<a href="services.html">Services</a>
<a href="blog.html">Blog</a>
<a href="contact.html">Contact Us</a> <a href="privacy-policy.html">Privacy Policy</a>
</div>
<div class="footer-col">
<h3>Contact</h3>
<a href="{GBP_URL}" target="_blank" rel="noopener" style="display:block;margin:0 0 8px;font-size:14px;">49, Labours Colony, Venkateswara Nagar, Koundampalayam, Coimbatore - 641030</a><a href="mailto:info@brandumax.com">info@brandumax.com</a>
<a href="tel:{PHONE_TEL}">{PHONE_DISP}</a>
</div>
</div>
<div class="footer-bottom">&copy; 2026 Brand U Max. All rights reserved.</div>
</footer>

<script src="assets/chatbot.js" defer></script>
<script src="assets/motion.js" defer></script>
<script src="assets/lead-capture.js" defer></script>
<a class="wa-float" href="{WA_LINK}" target="_blank" rel="noopener" aria-label="Chat with Brand U Max on WhatsApp">
<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.472,14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94,1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04,1.016-1.04,2.479 0,1.462 1.065,2.875 1.213,3.074.149.198 2.096,3.2 5.077,4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421,7.403h-.004a9.87,9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86,9.86 0 0 1-1.51-5.26c.001-5.45,4.436-9.884,9.888-9.884 2.64,0,5.122,1.03,6.988,2.898a9.825,9.825 0 0 1 2.893,6.994c-.003,5.45-4.437,9.884-9.885,9.884m8.413-18.297A11.815,11.815 0 0 0 12.05,0C5.495,0,.16,5.335.157,11.892c0,2.096.547,4.142 1.588,5.945L.057,24l6.305-1.654a11.882,11.882 0 0 0 5.683,1.448h.005c6.554,0,11.89-5.335,11.893-11.893a11.821,11.821 0 0 0-3.48-8.413Z"/></svg>
</a>
</body>
</html>
"""


def main():
    today = datetime.date.today()
    date_iso = today.isoformat()
    date_h = today.strftime("%B %d, %Y")
    try:
        trends = fetch_trends()
    except Exception as e:
        print(f"trend fetch failed ({e}); using evergreen fallback")
        trends = []
    trend = pick_trend(trends)
    print(f"analysis: fetched {len(trends)} trends")
    if trend:
        print(f"analysis: picked '{trend['title']}' ({trend['traffic']} searches)")
    else:
        print("analysis: no business-relevant trend, evergreen fallback")
    if trend:
        slug, headline, desc, points, faqs = trend_topic(trend)
        filename = f"blog-trend-{today.strftime('%Y%m%d')}-{slug}.html"
        tag = "trend"
    else:
        idx = today.timetuple().tm_yday % len(EVERGREEN)
        eslug, headline, desc, points = EVERGREEN[idx]
        filename = f"blog-trend-{today.strftime('%Y%m%d')}-{eslug}.html"
        faqs = (
            ("How fast should my business act on this?",
             "Same day. Local attention peaks last hours; a quick reel or GBP post beats a perfect campaign next week."),
            ("Will this bring enquiries or just views?",
             "Only if every post links to WhatsApp or a call page. Attention without a next step is vanity."),
            ("How does Brand U Max help?",
             "We run daily reels, GBP posts and Meta ads from Coimbatore so moments convert to leads."),
        )
        tag = "evergreen"
    path = ROOT / filename
    if path.exists():
        print(f"SKIP: {filename} already exists")
        return 0
    path.write_text(build_html(filename[:-5], headline, desc, points, faqs, date_h, date_iso),
                    encoding="utf-8")

    blog = ROOT / "blog.html"
    card = (f'<div class="card">\n<svg class="icon-svg" role="img" aria-label="{html.escape(headline)} icon" '
            'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>'
            f'<circle cx="12" cy="10" r="3"/></svg>\n<h3>{html.escape(headline)}</h3>\n'
            f'<p>{html.escape(meta_desc(desc))}</p>\n'
            f'<p style="opacity:.7;font-size:14px;">{date_h} &middot; 4 min read</p>\n'
            f'<a href="{filename}">Read More &rarr;</a>\n</div>\n')
    text = blog.read_text(encoding="utf-8")
    text = text.replace('<div class="grid">\n', '<div class="grid">\n' + card, 1)
    blog.write_text(text, encoding="utf-8")

    sm = ROOT / "sitemap.xml"
    stext = sm.read_text(encoding="utf-8")
    entry = (f'  <url><loc>https://brandumax.com/{filename}</loc>'
             f'<lastmod>{date_iso}</lastmod><changefreq>monthly</changefreq>'
             '<priority>0.5</priority></url>\n')
    stext = stext.replace("</urlset>", entry + "</urlset>", 1)
    sm.write_text(stext, encoding="utf-8")

    llms = ROOT / "llms.txt"
    ltext = llms.read_text(encoding="utf-8")
    ltext = ltext.replace("\n## Contact",
                          f"\n- [{headline}](https://brandumax.com/{filename}): {meta_desc(desc)}\n\n## Contact", 1)
    llms.write_text(ltext, encoding="utf-8")

    r = subprocess.run([sys.executable, "scripts/validate_site.py"], cwd=ROOT,
                       capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("validation failed, removing generated post")
        path.unlink(missing_ok=True)
        return 1
    print(f"CREATED ({tag}): {filename}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
