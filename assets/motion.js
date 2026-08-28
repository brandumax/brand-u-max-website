/* =============================================================================
   Brand U Max — motion system
   Scroll-triggered reveals, word-level heading stagger, and inertial smooth
   scrolling. No dependencies.

   Accessibility contract:
   - If this script never runs, nothing is hidden (see .no-js rules in CSS;
     the hiding styles only take effect once <html> gets .motion-ready).
   - prefers-reduced-motion disables every effect, including smooth scroll.
   - Smooth scroll never intercepts keyboard input, so keyboard and
     screen-reader navigation keep native behaviour.
   - A watchdog force-reveals anything still hidden after 3s.
   ========================================================================== */
(function () {
    'use strict';

    var root = document.documentElement;
    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var finePointer = window.matchMedia('(pointer: fine)').matches;

    // Only now does the CSS start hiding things — so a JS failure before this
    // point leaves the page fully readable.
    root.classList.add('motion-ready');

    /* ---------------------------------------------------------------------
       1. Split headings into words for staggered reveal
       --------------------------------------------------------------------- */
    function splitHeading(el) {
        // Only split plain-text headings; anything with child elements keeps
        // its markup intact rather than being flattened.
        if (el.children.length > 0) return false;
        var text = el.textContent.replace(/\s+/g, ' ').trim();
        if (!text) return false;

        var words = text.split(' ');
        var line = document.createElement('span');
        line.className = 'split-line';

        words.forEach(function (w, i) {
            var span = document.createElement('span');
            span.className = 'split-word';
            span.textContent = w;
            span.style.setProperty('--word-delay', (i * 55) + 'ms');
            line.appendChild(span);
            if (i < words.length - 1) line.appendChild(document.createTextNode(' '));
        });

        el.textContent = '';
        el.appendChild(line);
        return true;
    }

    /* ---------------------------------------------------------------------
       2. Decide what animates
       --------------------------------------------------------------------- */
    function markTargets() {
        // Headings get the word stagger
        document.querySelectorAll(
            '.hero h1, .page-hero h1, .section-header h2, .cta-band h2'
        ).forEach(function (el) {
            if (splitHeading(el)) el.setAttribute('data-reveal', 'text');
        });

        // Blocks that fade/rise in
        var blocks = [
            '.hero-eyebrow', '.hero p', '.hero .btn', '.hero-logo',
            '.page-hero p', '.page-hero .eyebrow',
            '.section-header .eyebrow', '.section-header p',
            '.cta-band p', '.cta-band .btn',
            '.faq-item', '.footer-col', '.breadcrumbs'
        ].join(',');
        document.querySelectorAll(blocks).forEach(function (el) {
            if (!el.hasAttribute('data-reveal')) el.setAttribute('data-reveal', '');
        });

        // Cards stagger within their own grid
        document.querySelectorAll('.grid').forEach(function (grid) {
            Array.prototype.forEach.call(grid.children, function (child, i) {
                child.setAttribute('data-reveal', '');
                child.style.setProperty('--reveal-delay', Math.min(i * 80, 480) + 'ms');
            });
        });

        // Standalone buttons in centred section blocks
        document.querySelectorAll('.section .container > div > .btn').forEach(function (el) {
            if (!el.hasAttribute('data-reveal')) el.setAttribute('data-reveal', '');
        });
    }

    /* ---------------------------------------------------------------------
       3. Reveal on scroll
       --------------------------------------------------------------------- */
    function show(el) { el.classList.add('is-visible'); }
    function hide(el) { el.classList.remove('is-visible'); }

    function initReveals() {
        var targets = document.querySelectorAll('[data-reveal]');

        if (reduceMotion || !('IntersectionObserver' in window)) {
            Array.prototype.forEach.call(targets, show);
            return;
        }

        // Reveals replay: an element animates in every time it enters the
        // viewport, and resets only once it has fully left. threshold 0 with a
        // shrunk bottom margin means it triggers just after entering from
        // below, and never flickers while any part of it is still on screen.
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) show(entry.target);
                else hide(entry.target);
            });
        }, { rootMargin: '0px 0px -10% 0px', threshold: 0 });

        Array.prototype.forEach.call(targets, function (el) { io.observe(el); });

        // Watchdog, and the crawler safety net.
        //
        // A visitor scrolls, moves a mouse, taps, or presses a key. A search
        // engine renderer does none of those and never scrolls -- so anything
        // still at opacity 0 because it never entered the viewport is invisible
        // to it, which here was three quarters of the homepage copy.
        //
        // Testing for any sign of a human, rather than for scrolling alone,
        // is what keeps the effect for someone who reads the hero for a while
        // before scrolling: they have almost certainly moved a pointer.
        var humanSeen = false;
        ['scroll', 'mousemove', 'wheel', 'pointerdown', 'touchstart', 'keydown']
            .forEach(function (evt) {
                window.addEventListener(evt, function () { humanSeen = true; },
                                        { passive: true, once: true });
            });

        window.setTimeout(function () {
            if (!humanSeen) {
                document.querySelectorAll('[data-reveal]').forEach(show);
                return;
            }
            // Someone is here: keep the effect, and only rescue anything on
            // screen that the observer somehow missed.
            document.querySelectorAll('[data-reveal]:not(.is-visible)').forEach(function (el) {
                var box = el.getBoundingClientRect();
                if (box.top < window.innerHeight && box.bottom > 0) show(el);
            });
        }, 2500);
    }

    /* ---------------------------------------------------------------------
       4. Inertial smooth scroll
       Wheel input is damped toward a target offset. Keyboard, touch and
       programmatic scrolling are deliberately left alone.
       --------------------------------------------------------------------- */
    function initSmoothScroll() {
        var target = window.scrollY;
        var current = target;
        var running = false;
        var EASE = 0.11;

        function maxScroll() {
            return Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
        }

        function frame() {
            var delta = target - current;
            if (Math.abs(delta) < 0.4) {
                current = target;
                window.scrollTo(0, Math.round(current));
                running = false;
                return;
            }
            current += delta * EASE;
            window.scrollTo(0, Math.round(current));
            requestAnimationFrame(frame);
        }

        function start() {
            if (!running) { running = true; requestAnimationFrame(frame); }
        }

        // If the pointer is over something that scrolls on its own (the chat
        // window, a code block, any overflow container), that element must keep
        // its native scrolling — we must not preventDefault over it.
        function overOwnScroller(node) {
            for (var el = node; el && el !== document.body && el !== document.documentElement; el = el.parentElement) {
                if (!(el instanceof Element)) continue;
                if (el.scrollHeight - el.clientHeight > 2) {
                    var oy = getComputedStyle(el).overflowY;
                    if (oy === 'auto' || oy === 'scroll') return true;
                }
            }
            return false;
        }

        window.addEventListener('wheel', function (e) {
            // Respect zoom and horizontal intent
            if (e.ctrlKey || e.metaKey) return;
            if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;
            if (overOwnScroller(e.target)) return;

            var delta = e.deltaY;
            if (e.deltaMode === 1) delta *= 16;        // lines -> px
            else if (e.deltaMode === 2) delta *= window.innerHeight;

            e.preventDefault();
            target = Math.min(Math.max(target + delta, 0), maxScroll());
            start();
        }, { passive: false });

        // Re-sync whenever anything other than the wheel moves the page
        // (keyboard, scrollbar drag, anchor jumps, find-in-page).
        window.addEventListener('scroll', function () {
            if (!running) { target = window.scrollY; current = target; }
        }, { passive: true });

        window.addEventListener('resize', function () {
            target = Math.min(target, maxScroll());
        });

        root.classList.add('has-smooth-scroll');
    }

    /* ---------------------------------------------------------------------
       5. Boot
       --------------------------------------------------------------------- */
    function boot() {
        markTargets();
        initReveals();
        // Inertia only where it helps: a real pointer, and motion allowed.
        // Touch devices already have excellent native momentum scrolling.
        if (!reduceMotion && finePointer) initSmoothScroll();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
