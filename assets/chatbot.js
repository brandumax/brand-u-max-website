(function () {
  var faq = [
    { k: ['hello', 'hi', 'hey'], a: "Hi there! I'm the Brand U Max assistant. Ask me about our services, pricing, or how to get in touch." },
    { k: ['service', 'seo', 'ppc', 'advertis', 'social media', 'brand', 'content', 'conversion', 'analytics'], a: "We offer SEO & Content, Paid Advertising, Social Media Marketing, Branding & Creative, Conversion Optimization and Analytics & Reporting. Check out the full Services page for details." },
    { k: ['price', 'cost', 'pricing', 'quote', 'budget'], a: "Pricing depends on your goals and channels. The best next step is a free marketing audit - just head to our Contact page to request one." },
    { k: ['audit'], a: "You can get a free marketing audit by visiting our Contact page and sending us a message, or calling us directly." },
    { k: ['contact', 'email', 'phone', 'call', 'reach', 'number', 'whatsapp', 'mobile'], a: "You can reach us at brandmaxtool@gmail.com or call +91 7401555777. Office hours are Monday to Saturday, 9:00 AM to 6:00 PM." },
    { k: ['hour', 'open', 'time'], a: "Our office hours are Monday to Saturday, 9:00 AM to 6:00 PM." },
    { k: ['about', 'who are you', 'company', 'mission'], a: "Brand U Max is a digital marketing agency focused on growth, revenue and profit, not just vanity metrics. Visit our About page to learn more." },
    { k: ['thank'], a: "You're welcome! Let us know if there's anything else you'd like to know." }
  ];

  function findAnswer(text) {
    var lower = text.toLowerCase();
    for (var i = 0; i < faq.length; i++) {
      for (var j = 0; j < faq[i].k.length; j++) {
        if (lower.indexOf(faq[i].k[j]) !== -1) {
          return faq[i].a;
        }
      }
    }
    return "I'm not totally sure about that one. For anything specific, please reach out on our Contact page and our team will help you directly.";
  }

  function addMessage(container, text, who) {
    var msg = document.createElement('div');
    msg.className = 'bumax-msg bumax-msg-' + who;
    msg.textContent = text;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var style = document.createElement('style');
    style.textContent = ''
      + '.bumax-chat-btn{position:fixed;bottom:24px;right:24px;width:60px;height:60px;border-radius:50%;background:var(--navy,#1b2a4a);color:#fff;display:flex;align-items:center;justify-content:center;font-size:28px;cursor:pointer;box-shadow:0 10px 30px rgba(27,42,74,0.35);z-index:9999;border:none;}'
      + '.bumax-chat-window{position:fixed;bottom:96px;right:24px;width:320px;max-width:88vw;max-height:70vh;background:#fff;border-radius:14px;box-shadow:0 10px 30px rgba(27,42,74,0.25);display:none;flex-direction:column;overflow:hidden;z-index:9999;font-family:Segoe UI,Arial,sans-serif;}'
      + '.bumax-chat-window.open{display:flex;}'
      + '.bumax-chat-header{background:var(--navy,#1b2a4a);color:#fff;padding:14px 16px;font-weight:700;display:flex;justify-content:space-between;align-items:center;}'
      + '.bumax-chat-close{cursor:pointer;font-size:18px;line-height:1;background:none;border:none;color:#fff;}'
      + '.bumax-chat-body{flex:1;padding:12px;overflow-y:auto;background:#f7f8fb;display:flex;flex-direction:column;}'
      + '.bumax-msg{margin-bottom:10px;padding:8px 12px;border-radius:10px;max-width:85%;font-size:14px;line-height:1.4;}'
      + '.bumax-msg-bot{background:#e9edf5;color:#1b2a4a;align-self:flex-start;}'
      + '.bumax-msg-user{background:var(--orange,#f5a623);color:#1b2a4a;align-self:flex-end;margin-left:auto;}'
      + '.bumax-chat-input-row{display:flex;border-top:1px solid #eee;padding:8px;gap:8px;}'
      + '.bumax-chat-input{flex:1;border:1px solid #ddd;border-radius:20px;padding:8px 12px;font-size:14px;outline:none;}'
      + '.bumax-chat-send{background:var(--orange,#f5a623);border:none;color:#1b2a4a;font-weight:700;border-radius:20px;padding:8px 14px;cursor:pointer;}';
    document.head.appendChild(style);

    var btn = document.createElement('button');
    btn.className = 'bumax-chat-btn';
    btn.setAttribute('aria-label', 'Open chat');
    btn.textContent = String.fromCodePoint(0x1F4AC);

    var win = document.createElement('div');
    win.className = 'bumax-chat-window';
    win.innerHTML = ''
      + '<div class="bumax-chat-header"><span>Brand U Max Assistant</span><button class="bumax-chat-close" aria-label="Close chat">&times;</button></div>'
      + '<div class="bumax-chat-body"></div>'
      + '<div class="bumax-chat-input-row"><input type="text" class="bumax-chat-input" placeholder="Ask about services, pricing..."><button class="bumax-chat-send">Send</button></div>';

    document.body.appendChild(btn);
    document.body.appendChild(win);

    var body = win.querySelector('.bumax-chat-body');
    var input = win.querySelector('.bumax-chat-input');
    var sendBtn = win.querySelector('.bumax-chat-send');
    var closeBtn = win.querySelector('.bumax-chat-close');

    var greeted = false;

    btn.addEventListener('click', function () {
      win.classList.toggle('open');
      if (win.classList.contains('open') && !greeted) {
        addMessage(body, "Hi! I'm the Brand U Max assistant. Ask me about our services, pricing, office hours, or how to get in touch.", 'bot');
        greeted = true;
      }
    });

    closeBtn.addEventListener('click', function () {
      win.classList.remove('open');
    });

    function handleSend() {
      var text = input.value.trim();
      if (!text) return;
      addMessage(body, text, 'user');
      input.value = '';
      setTimeout(function () {
        addMessage(body, findAnswer(text), 'bot');
      }, 300);
    }

    sendBtn.addEventListener('click', handleSend);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        handleSend();
      }
    });
  });
})();
