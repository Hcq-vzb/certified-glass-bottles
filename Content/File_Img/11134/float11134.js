(function () {
  if (document.getElementById("kiwl-chat-widget")) return;

  var WHATSAPP_URL = "https://wa.me/8617751189576";
  var COMPANY = "Jiangsu KIWL Machinery Manufacturing Group Co., Ltd.";
  var BRAND = "KIWL";

  var replies = {
    about: {
      text:
        "We are a specialist in selling and exporting packaging materials to the domestic and international alcoholic beverage industry. With <strong>over 20 years of experience</strong>, our team delivers one-stop packaging solutions trusted in <strong>70+ countries</strong>.",
      followUp:
        "We combine glass bottle factories, cap factories, label makers and paper tube box manufacturers into one solid group — focused on professional packaging solutions for every customer.",
    },
    products: {
      text:
        "Our main products include:<br>• Glass Bottles (wine, spirits, olive oil & more)<br>• Bottle Caps (aluminium, plastic, screw, GPI, Guala)<br>• Bottle Stoppers & Synthetic Corks<br>• Metal Labels & Paper Labels<br>• Custom Paper Tube Boxes",
      followUp:
        "Need customization on lids, labels or packaging? Our sales manager can recommend the right solution for your brand.",
    },
    quote: {
      text:
        "We'd love to help with pricing, MOQ, lead time and custom design. Share your product details and our sales manager will reply on WhatsApp — usually within a few hours during business days.",
      followUp: null,
    },
    default: {
      text:
        "Searching for a one-stop shop for bottle caps, labels and paper boxes? KIWL is your best option — unmatched competence in production, service and customisation as a top bottle cap producer.",
      followUp:
        "Tell us what you need and we'll connect you with our sales team right away.",
    },
  };

  var css =
    "#kiwl-chat-widget{font-family:Arial,Helvetica,sans-serif;z-index:99999;line-height:1.4}" +
    "#kiwl-chat-widget *{box-sizing:border-box}" +
    ".kiwl-chat-toggle{position:fixed;right:20px;bottom:24px;width:58px;height:58px;border:none;border-radius:50%;background:linear-gradient(135deg,#1a5fb4,#0d3d7a);color:#fff;cursor:pointer;box-shadow:0 4px 18px rgba(13,61,122,.35);display:flex;align-items:center;justify-content:center;transition:transform .2s,box-shadow .2s;z-index:99999}" +
    ".kiwl-chat-toggle:hover{transform:scale(1.06);box-shadow:0 6px 22px rgba(13,61,122,.45)}" +
    ".kiwl-chat-toggle svg{width:28px;height:28px;fill:currentColor}" +
    ".kiwl-chat-toggle.is-open{background:#555}" +
    ".kiwl-chat-panel{position:fixed;right:20px;bottom:92px;width:360px;max-width:calc(100vw - 32px);height:520px;max-height:calc(100vh - 120px);background:#fff;border-radius:14px;box-shadow:0 8px 40px rgba(0,0,0,.18);display:flex;flex-direction:column;overflow:hidden;opacity:0;visibility:hidden;transform:translateY(16px) scale(.96);transition:opacity .25s,transform .25s,visibility .25s;z-index:99998}" +
    ".kiwl-chat-panel.is-open{opacity:1;visibility:visible;transform:translateY(0) scale(1)}" +
    ".kiwl-chat-head{background:linear-gradient(135deg,#1a5fb4,#0d3d7a);color:#fff;padding:14px 16px;display:flex;align-items:center;gap:12px;flex-shrink:0}" +
    ".kiwl-chat-avatar{width:42px;height:42px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;color:#0d3d7a;flex-shrink:0}" +
    ".kiwl-chat-head-info{flex:1;min-width:0}" +
    ".kiwl-chat-head-info strong{display:block;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
    ".kiwl-chat-head-info span{font-size:12px;opacity:.9}" +
    ".kiwl-chat-close{background:rgba(255,255,255,.15);border:none;color:#fff;width:32px;height:32px;border-radius:50%;cursor:pointer;font-size:20px;line-height:1;flex-shrink:0}" +
    ".kiwl-chat-close:hover{background:rgba(255,255,255,.28)}" +
    ".kiwl-chat-messages{flex:1;overflow-y:auto;padding:16px;background:#f4f6f9;display:flex;flex-direction:column;gap:10px}" +
    ".kiwl-msg{max-width:88%;padding:10px 14px;border-radius:12px;font-size:13px;color:#333;animation:kiwlFadeIn .35s ease}" +
    "@keyframes kiwlFadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}" +
    ".kiwl-msg-bot{background:#fff;border:1px solid #e5e9ef;border-bottom-left-radius:4px;align-self:flex-start}" +
    ".kiwl-msg-bot strong{color:#0d3d7a}" +
    ".kiwl-msg-user{background:#dce8f8;border-bottom-right-radius:4px;align-self:flex-end;color:#1a3a5c}" +
    ".kiwl-msg-typing{align-self:flex-start;background:#fff;border:1px solid #e5e9ef;padding:12px 16px;border-radius:12px;border-bottom-left-radius:4px}" +
    ".kiwl-msg-typing span{display:inline-block;width:7px;height:7px;background:#aaa;border-radius:50%;margin:0 2px;animation:kiwlDot 1.2s infinite}" +
    ".kiwl-msg-typing span:nth-child(2){animation-delay:.2s}" +
    ".kiwl-msg-typing span:nth-child(3){animation-delay:.4s}" +
    "@keyframes kiwlDot{0%,80%,100%{opacity:.3;transform:scale(.8)}40%{opacity:1;transform:scale(1)}}" +
    ".kiwl-chat-quick{padding:10px 12px 4px;display:flex;flex-wrap:wrap;gap:8px;background:#fff;border-top:1px solid #e5e9ef;flex-shrink:0}" +
    ".kiwl-chat-quick button{border:1px solid #1a5fb4;background:#fff;color:#1a5fb4;border-radius:18px;padding:7px 14px;font-size:12px;cursor:pointer;transition:background .2s,color .2s}" +
    ".kiwl-chat-quick button:hover{background:#1a5fb4;color:#fff}" +
    ".kiwl-chat-quick.is-hidden{display:none}" +
    ".kiwl-chat-foot{padding:12px;background:#fff;border-top:1px solid #e5e9ef;flex-shrink:0}" +
    ".kiwl-wa-btn{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:12px 16px;border:none;border-radius:10px;background:#25d366;color:#fff;font-size:14px;font-weight:600;text-decoration:none;cursor:pointer;transition:background .2s}" +
    ".kiwl-wa-btn:hover{background:#1ebe57;color:#fff}" +
    ".kiwl-wa-btn svg{width:20px;height:20px;fill:currentColor;flex-shrink:0}" +
    "@media(max-width:768px){.kiwl-chat-toggle{right:16px;bottom:72px;width:52px;height:52px}.kiwl-chat-panel{right:16px;bottom:136px;height:460px}}";

  var chatIcon =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>';
  var closeIcon = "×";
  var waIcon =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.435 9.884-9.881 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>';

  var html =
    '<div id="kiwl-chat-widget">' +
    '<style>' +
    css +
    "</style>" +
    '<button type="button" class="kiwl-chat-toggle" id="kiwlChatToggle" aria-label="Open chat support" title="Chat with us">' +
    chatIcon +
    "</button>" +
    '<div class="kiwl-chat-panel" id="kiwlChatPanel" role="dialog" aria-label="KIWL customer support chat">' +
    '<div class="kiwl-chat-head">' +
    '<div class="kiwl-chat-avatar">' +
    BRAND +
    "</div>" +
    '<div class="kiwl-chat-head-info"><strong>' +
    COMPANY +
    '</strong><span>Online Support · Typically replies quickly</span></div>' +
    '<button type="button" class="kiwl-chat-close" id="kiwlChatClose" aria-label="Close chat">' +
    closeIcon +
    "</button>" +
    "</div>" +
    '<div class="kiwl-chat-messages" id="kiwlChatMessages"></div>' +
    '<div class="kiwl-chat-quick" id="kiwlChatQuick">' +
    '<button type="button" data-key="about">About KIWL</button>' +
    '<button type="button" data-key="products">Our Products</button>' +
    '<button type="button" data-key="quote">Get a Quote</button>' +
    "</div>" +
    '<div class="kiwl-chat-foot">' +
    '<a class="kiwl-wa-btn" id="kiwlWaBtn" href="' +
    WHATSAPP_URL +
    '" target="_blank" rel="nofollow noopener">' +
    waIcon +
    "Chat on WhatsApp with Sales Manager</a>" +
    "</div>" +
    "</div></div>";

  document.body.insertAdjacentHTML("beforeend", html);

  var toggle = document.getElementById("kiwlChatToggle");
  var panel = document.getElementById("kiwlChatPanel");
  var closeBtn = document.getElementById("kiwlChatClose");
  var messages = document.getElementById("kiwlChatMessages");
  var quick = document.getElementById("kiwlChatQuick");
  var started = false;
  var busy = false;

  function scrollBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  function addBotMessage(htmlText) {
    var el = document.createElement("div");
    el.className = "kiwl-msg kiwl-msg-bot";
    el.innerHTML = htmlText;
    messages.appendChild(el);
    scrollBottom();
    return el;
  }

  function addUserMessage(text) {
    var el = document.createElement("div");
    el.className = "kiwl-msg kiwl-msg-user";
    el.textContent = text;
    messages.appendChild(el);
    scrollBottom();
    return el;
  }

  function showTyping() {
    var el = document.createElement("div");
    el.className = "kiwl-msg-typing";
    el.id = "kiwlTyping";
    el.innerHTML = "<span></span><span></span><span></span>";
    messages.appendChild(el);
    scrollBottom();
    return el;
  }

  function hideTyping() {
    var el = document.getElementById("kiwlTyping");
    if (el) el.remove();
  }

  function delay(ms) {
    return new Promise(function (resolve) {
      setTimeout(resolve, ms);
    });
  }

  function botSay(htmlText, wait) {
    return delay(wait || 700).then(function () {
      hideTyping();
      addBotMessage(htmlText);
    });
  }

  function startConversation() {
    if (started) return;
    started = true;
    showTyping();
    botSay(
      "Hello! 👋 Welcome to <strong>" +
        BRAND +
        "</strong>.<br><br>We provide one-stop packaging solutions for the global alcoholic beverage industry — glass bottles, caps, stoppers, labels & paper boxes.",
      900
    ).then(function () {
      showTyping();
      return botSay(
        "How can we help you today? Choose a topic below, or tap the green button to speak with our <strong>sales manager on WhatsApp</strong>.",
        1100
      );
    });
  }

  function handleReply(key, label) {
    if (busy) return;
    busy = true;
    quick.classList.add("is-hidden");
    addUserMessage(label);

    var data = replies[key] || replies.default;
    showTyping();

    botSay(data.text, 900).then(function () {
      if (data.followUp) {
        showTyping();
        return botSay(data.followUp, 1000);
      }
    }).then(function () {
      showTyping();
      return botSay(
        'Ready to move forward? Click <strong>"Chat on WhatsApp with Sales Manager"</strong> below — we will assist you with quotes, samples and custom packaging.',
        800
      );
    }).then(function () {
      busy = false;
      quick.classList.remove("is-hidden");
    });
  }

  function openChat() {
    panel.classList.add("is-open");
    toggle.classList.add("is-open");
    toggle.setAttribute("aria-label", "Close chat support");
    startConversation();
  }

  function closeChat() {
    panel.classList.remove("is-open");
    toggle.classList.remove("is-open");
    toggle.setAttribute("aria-label", "Open chat support");
  }

  toggle.addEventListener("click", function () {
    if (panel.classList.contains("is-open")) closeChat();
    else openChat();
  });

  closeBtn.addEventListener("click", closeChat);

  quick.addEventListener("click", function (e) {
    var btn = e.target.closest("button[data-key]");
    if (!btn) return;
    handleReply(btn.getAttribute("data-key"), btn.textContent.trim());
  });

  document.getElementById("kiwlWaBtn").addEventListener("click", function () {
    var msg =
      "Hello, I visited your website (www.certifiedglassbottles.com) and would like to inquire about packaging products. Please assist me.";
    this.href = WHATSAPP_URL + "?text=" + encodeURIComponent(msg);
  });
})();
