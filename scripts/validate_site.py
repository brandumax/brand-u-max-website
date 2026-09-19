"""Validate the static site. Usage: python scripts/validate_site.py  (exit 1 on any failure)."""
import glob, io, json, re, sys
from html.parser import HTMLParser
import xml.dom.minidom

class Balance(HTMLParser):
    TRACK = ('div', 'section', 'a')
    def __init__(self):
        super().__init__()
        self.count = {t: 0 for t in self.TRACK}
    def handle_starttag(self, tag, attrs):
        if tag in self.count: self.count[tag] += 1
    def handle_endtag(self, tag):
        if tag in self.count: self.count[tag] -= 1

errors = []
for f in sorted(glob.glob('*.html')):
    s = io.open(f, encoding='utf-8').read()
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try: json.loads(m.group(1))
        except ValueError as e: errors.append(f'{f}: invalid JSON-LD ({e})')
    b = Balance(); b.feed(s)
    for t, n in b.count.items():
        if n: errors.append(f'{f}: unbalanced <{t}> ({n:+d})')
    d = re.search(r'<meta name="description" content="([^"]*)"', s)
    if not d: errors.append(f'{f}: no meta description')
    elif len(d.group(1)) > 140: errors.append(f'{f}: meta description {len(d.group(1))} chars (>140)')
    if len(re.findall(r'<h1[\s>]', s)) != 1: errors.append(f'{f}: expected exactly one <h1>')
    if '`n' in s: errors.append(f'{f}: stray `n')
    if 'href="style.css?v=' not in s: errors.append(f'{f}: stylesheet not versioned')
    if 'X-Content-Type-Options' not in s: errors.append(f'{f}: missing nosniff meta')
    if 'consent.js' not in s: errors.append(f'{f}: consent.js not loaded')
    for tag in re.findall(r'<img\b[^>]*>', s):
        if 'width=' not in tag or 'height=' not in tag: errors.append(f'{f}: <img> without width/height')
        if 'alt=' not in tag: errors.append(f'{f}: <img> without alt')
try: xml.dom.minidom.parse('sitemap.xml')
except Exception as e: errors.append(f'sitemap.xml: {e}')
print('\n'.join(errors) if errors else 'OK: all checks passed')
sys.exit(1 if errors else 0)
