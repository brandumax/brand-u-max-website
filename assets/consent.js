/* Cookie consent + consent-gated Google Analytics (GA4). No external library.
   gtag() is stubbed in each page's <head>; the GA script only loads after "Accept". */
(function () {
  var GA_ID = 'G-7RNMPLX6D3';
  var KEY = 'bumax-consent';

  function read() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function save(v) {
    try { localStorage.setItem(KEY, v); } catch (e) { /* ignore */ }
  }

  function loadAnalytics() {
    if (window.__bumaxGA) return;
    window.__bumaxGA = true;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    gtag('js', new Date());
    gtag('config', GA_ID);
  }

  function showBanner() {
    var bar = document.createElement('div');
    bar.className = 'consent-banner';
    bar.setAttribute('role', 'dialog');
    bar.setAttribute('aria-label', 'Cookie consent');
    bar.innerHTML = ''
      + '<p>We use cookies for analytics to understand how visitors use this site. '
      + '<a href="privacy-policy.html">Privacy Policy</a></p>'
      + '<div class="consent-actions">'
      + '<button type="button" class="btn btn-outline" data-consent="declined">Decline</button>'
      + '<button type="button" class="btn btn-primary" data-consent="granted">Accept</button>'
      + '</div>';
    bar.addEventListener('click', function (e) {
      var choice = e.target && e.target.getAttribute && e.target.getAttribute('data-consent');
      if (!choice) return;
      save(choice);
      if (choice === 'granted') loadAnalytics();
      bar.parentNode.removeChild(bar);
    });
    document.body.appendChild(bar);
  }

  if (read() === 'granted') {
    loadAnalytics();
  } else if (read() !== 'declined') {
    document.addEventListener('DOMContentLoaded', showBanner);
  }
})();
