(function () {
  function track(event, params) {
    if (typeof gtag === 'function') {
      try { gtag('event', event, params || {}); } catch (e) { /* ignore */ }
    }
    if (typeof dataLayer !== 'undefined') {
      try { dataLayer.push({ event: event, ...(params || {}) }); } catch (e) { /* ignore */ }
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-ga-event]').forEach(function (el) {
      el.addEventListener('click', function (e) {
        track(el.getAttribute('data-ga-event'), {
          page: location.pathname,
          href: el.getAttribute('href') || ''
        });
      });
    });

    document.querySelectorAll('a.btn, .nav-cta, .wa-float').forEach(function (el) {
      el.addEventListener('click', function (e) {
        var href = el.getAttribute('href') || '';
        var cls = el.className || '';
        var eventName = 'cta_click';
        if (href.indexOf('wa.me') !== -1 || cls.indexOf('whatsapp') !== -1 || cls.indexOf('wa-float') !== -1) {
          eventName = 'cta_whatsapp';
        } else if (href.indexOf('contact') !== -1 || href.indexOf('tel:') !== -1 || href.indexOf('mailto:') !== -1) {
          eventName = 'cta_contact';
        } else if (cls.indexOf('btn-outline') !== -1) {
          eventName = 'cta_explore';
        } else {
          eventName = 'cta_primary';
        }
        track(eventName, { page: location.pathname, href: href });
      });
    });

    var form = document.querySelector('.lead-form');
    if (form) {
      var phone = form.getAttribute('data-lead-phone') || '917401555777';
      var submit = document.getElementById('lead-submit');
      var note = document.getElementById('lead-note');

      submit.addEventListener('click', function () {
        var name = (document.getElementById('lead-name') || {}).value || '';
        var email = (document.getElementById('lead-email') || {}).value || '';

        document.getElementById('lead-name').setCustomValidity('');
        if (!name || !form.reportValidity) {
          form.classList.add('was-validated');
        }
        if (!name.trim()) {
          document.getElementById('lead-name').focus();
          return;
        }
        var emailInput = document.getElementById('lead-email');
        if (emailInput && emailInput.type === 'email' && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(emailInput.value)) {
          emailInput.setCustomValidity('Please enter a valid email address.');
          emailInput.reportValidity();
          return;
        }

        var msg = 'Hi Brand U Max, please send me the free digital marketing audit checklist.'
          + ' My name: ' + name + '. Email: ' + email;
        var waUrl = 'https://wa.me/' + phone + '?text=' + encodeURIComponent(msg);

        // Lead event fires only here, on a validated submit (not on the raw button click).
        track('lead_magnet_email', { page: location.pathname });

        var opened = window.open(waUrl, '_blank');
        if (note) {
          note.setAttribute('role', 'status');
          note.setAttribute('aria-live', 'polite');
          note.style.opacity = '1';
          note.style.fontWeight = '600';
          if (opened) {
            note.textContent = "Thanks! We've opened WhatsApp — just press send and we'll deliver the checklist right away.";
          } else {
            note.textContent = 'Thanks! Your browser blocked the WhatsApp window — ';
            var link = document.createElement('a');
            link.href = waUrl;
            link.target = '_blank';
            link.rel = 'noopener';
            link.textContent = 'tap here to open WhatsApp and press send.';
            note.appendChild(link);
          }
        }
        if (typeof form.reset === 'function') { form.reset(); }
      });
    }
  });
})();