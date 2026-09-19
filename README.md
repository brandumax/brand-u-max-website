# brand-u-max-website

Official website for Brand U Max, an AI business growth consultant (https://brandumax.com).

This repo is a plain static site: hand-written HTML, one shared `style.css`, and a few small scripts in `assets/`. There is no build step and no backend.

## Preview locally

```bash
python -m http.server 8000
```

Then open http://localhost:8000. Opening `index.html` directly also works, but root-relative links such as `/` only resolve correctly through a local server.

## Deploy

Hosting is GitHub Pages with the custom domain in `CNAME`. Push to `main` and the site is live at https://brandumax.com within about 60 seconds. There is nothing to build.

After changing `style.css`, bump the `?v=` number on the stylesheet link in every page so visitors do not get a cached copy.

## Structure

- `*.html` pages; blog posts are `blog-*.html`
- `style.css` shared styles
- `assets/` images, video, and scripts (`consent.js` cookie banner + analytics gate, `chatbot.js`, `lead-capture.js`, `motion.js`)
- `sitemap.xml`, `robots.txt`, `llms.txt` for crawlers and AI tools

## Contact form setup

`contact.html` posts to Formspree. Replace `YOUR_FORM_ID` in the form's `action` URL with your Formspree form ID.

## Validation scripts

Both live in `scripts/`:

```bash
python scripts/validate_site.py   # JSON-LD parses, tags balanced, one <h1>, meta description <= 140 chars, images sized, sitemap valid
node scripts/test_chatbot.js      # chatbot keyword matching tests
```

Run both before pushing.
