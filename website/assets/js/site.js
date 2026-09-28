/* Mark LIV website behaviour. No dependencies. Everything degrades gracefully without JS. */
(function () {
  'use strict';
  var S = window.SITE || {};
  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var placeholder = /YOUR-USERNAME|example\.com|Your Name/;

  /* ── header ───────────────────────────────────────────────────────────── */
  var header = $('.site-header');
  function onScroll() { if (header) header.classList.toggle('scrolled', window.scrollY > 8); }
  onScroll(); window.addEventListener('scroll', onScroll, { passive: true });

  var toggle = $('.nav-toggle'), links = $('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    links.addEventListener('click', function (e) { if (e.target.closest('a')) { links.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); } });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { links.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); } });
  }
  $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

  /* ── config-driven text and links ─────────────────────────────────────── */
  var repoOk = /^[\w.-]+\/[\w.-]+$/.test(S.repo || '');
  var repoUrl = repoOk ? 'https://github.com/' + S.repo : '#';
  $$('[data-repo]').forEach(function (a) { a.href = repoUrl; });
  $$('[data-issues]').forEach(function (a) { a.href = repoUrl + '/issues'; });
  $$('[data-discussions]').forEach(function (a) { a.href = repoUrl + '/discussions'; });
  $$('[data-releases]').forEach(function (a) { a.href = repoUrl + '/releases'; });
  $$('[data-email]').forEach(function (a) { a.href = 'mailto:' + S.email; if (!a.textContent.trim()) a.textContent = S.email; });
  $$('[data-email-text]').forEach(function (el) { el.textContent = S.email; });
  $$('[data-owner]').forEach(function (el) { el.textContent = S.owner; });
  $$('[data-version]').forEach(function (el) { el.textContent = S.version; });
  $$('[data-config-banner]').forEach(function (el) {
    var unset = placeholder.test(S.repo + ' ' + S.url + ' ' + S.email + ' ' + S.owner);
    el.hidden = !unset;
  });

  /* ── OS detection ─────────────────────────────────────────────────────── */
  function detectOS() {
    var ua = navigator.userAgent || '';
    var plat = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || '';
    var s = (plat + ' ' + ua).toLowerCase();
    if (/android/.test(s)) return 'mobile';
    if (/iphone|ipad|ipod/.test(s) || (/mac/.test(s) && navigator.maxTouchPoints > 1)) return 'mobile';
    if (/win/.test(s)) return 'windows';
    if (/mac/.test(s)) return 'mac';
    if (/linux|x11|cros/.test(s)) return 'linux';
    return 'other';
  }
  var os = detectOS();
  var macArch = 'mac-arm';       // Apple silicon is the safe default today
  function resolveKey(k) { return k === 'mac' ? macArch : k; }

  function paintDownloads() {
    var auto = os === 'windows' ? 'windows' : os === 'mac' ? resolveKey('mac') : os === 'linux' ? 'linux' : null;
    var meta = auto && S.assets ? S.assets[auto] : null;
    $$('[data-dl]').forEach(function (a) {
      var key = a.getAttribute('data-dl');
      if (key === 'auto') {
        if (meta && repoOk) {
          a.href = repoUrl + '/releases/latest/download/' + meta.file;
          var l = $('[data-dl-label]', a); if (l) l.textContent = 'Download for ' + meta.label;
        } else {
          a.href = 'download.html';
          var l2 = $('[data-dl-label]', a);
          if (l2) l2.textContent = os === 'mobile' ? 'Get it for your computer' : 'Download';
        }
        return;
      }
      var m = S.assets && S.assets[key];
      if (m) a.href = repoOk ? repoUrl + '/releases/latest/download/' + m.file : '#';
    });
    $$('[data-os-note]').forEach(function (el) {
      el.textContent = os === 'mobile' ? 'Mark LIV runs on Windows, macOS and Linux computers. Open this page on your laptop to download.'
        : meta ? meta.note + ' · Free' : 'Windows, macOS and Linux · Free';
    });
    $$('.os').forEach(function (card) {
      var k = card.getAttribute('data-os');
      var match = (k === 'windows' && os === 'windows') || (k === 'mac' && os === 'mac') || (k === 'linux' && os === 'linux');
      card.classList.toggle('match', match);
      var b = $('.badge', card); if (b) b.hidden = !match;
    });
  }
  paintDownloads();
  if (navigator.userAgentData && navigator.userAgentData.getHighEntropyValues && os === 'mac') {
    navigator.userAgentData.getHighEntropyValues(['architecture']).then(function (v) {
      if (v && v.architecture === 'x86') { macArch = 'mac-x64'; paintDownloads(); }
    }).catch(function () {});
  }

  /* ── latest release info from GitHub (cached, optional) ───────────────── */
  function fmtMB(b) { return b ? (b / 1048576 >= 100 ? Math.round(b / 1048576) : (b / 1048576).toFixed(1)) + ' MB' : ''; }
  function applyRelease(r) {
    if (!r) return;
    var v = String(r.tag_name || '').replace(/^v/i, '');
    if (v) $$('[data-version]').forEach(function (el) { el.textContent = v; });
    if (r.published_at) {
      var d = new Date(r.published_at);
      $$('[data-release-date]').forEach(function (el) { el.textContent = d.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }); });
    }
    $$('[data-release-notes]').forEach(function (a) { if (/^https:\/\/github\.com\//.test(r.html_url || '')) a.href = r.html_url; });
    (r.assets || []).forEach(function (asset) {
      Object.keys(S.assets || {}).forEach(function (key) {
        if (S.assets[key].file === asset.name) $$('[data-size="' + key + '"]').forEach(function (el) { el.textContent = fmtMB(asset.size); });
      });
    });
  }
  if (repoOk && !placeholder.test(S.repo) && $('[data-version], [data-size]')) {
    var cacheKey = 'ml_release_' + S.repo, cached = null;
    try { cached = JSON.parse(sessionStorage.getItem(cacheKey) || 'null'); } catch (e) {}
    if (cached && Date.now() - cached.t < 30 * 60 * 1000) applyRelease(cached.r);
    else fetch('https://api.github.com/repos/' + S.repo + '/releases/latest', { headers: { Accept: 'application/vnd.github+json' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (r) { if (r) { try { sessionStorage.setItem(cacheKey, JSON.stringify({ t: Date.now(), r: r })); } catch (e) {} applyRelease(r); } })
      .catch(function () {});
  }

  /* ── reveal on scroll + card spotlight ────────────────────────────────── */
  var reveals = $$('.reveal');
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  } else reveals.forEach(function (el) { el.classList.add('in'); });
  $$('.card').forEach(function (c) {
    c.addEventListener('pointermove', function (e) {
      var r = c.getBoundingClientRect();
      c.style.setProperty('--mx', (e.clientX - r.left) + 'px'); c.style.setProperty('--my', (e.clientY - r.top) + 'px');
    });
  });

  /* ── landing demo: a chat that types itself ───────────────────────────── */
  var demo = $('#demo');
  if (demo) {
    var scripts = {
      voice: [['u', 'Hey Jarvis, open Spotify and turn the volume down to 30.'], ['a', 'open_app → Spotify   ·   computer_settings → volume 30%'], ['j', 'Done. Spotify is open and the volume is at thirty percent.']],
      vision: [['u', 'What\u2019s on my screen?'], ['a', 'screen_processor → capture'], ['j', 'You have a spreadsheet of Q3 sales by region. The West is up twelve percent and the East is flat. Want a summary?']],
      control: [['u', 'Organise my desktop.'], ['a', 'file_controller → organize_desktop'], ['j', 'Sorted 42 files into folders. Say \u201Cundo\u201D and I\u2019ll put every one back.'], ['u', 'Undo.'], ['a', 'undo → restored 42 files'], ['j', 'All back where they were.']],
      remote: [['u', 'Remind me to call Sam at six.'], ['a', 'reminder → 18:00  (from phone dashboard)'], ['j', 'Reminder set for six p.m. It will pop up on your computer.']]
    };
    var screen = $('#demo-screen'), tabs = $$('.demo-tab', demo), timer = null, run = 0;
    function esc(t) { return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
    function play(key) {
      var id = ++run; clearTimeout(timer); screen.innerHTML = '';
      var lines = scripts[key] || [], i = 0;
      (function next() {
        if (id !== run || i >= lines.length) return;
        var l = lines[i++], el = document.createElement('div'); el.className = l[0] === 'u' ? 'u' : l[0] === 'a' ? 'act' : 'j';
        screen.appendChild(el);
        if (reduce || l[0] === 'a') { el.textContent = l[1]; timer = setTimeout(next, reduce ? 0 : 500); return; }
        var n = 0; el.classList.add('caret');
        (function type() {
          if (id !== run) return;
          n += 2; el.textContent = l[1].slice(0, n);
          if (n < l[1].length) timer = setTimeout(type, 18);
          else { el.classList.remove('caret'); timer = setTimeout(next, 520); }
        })();
      })();
    }
    tabs.forEach(function (t) { t.addEventListener('click', function () {
      tabs.forEach(function (x) { x.setAttribute('aria-selected', String(x === t)); }); play(t.getAttribute('data-demo'));
    }); });
    if ('IntersectionObserver' in window) {
      var seen = new IntersectionObserver(function (en) { if (en[0].isIntersecting) { play('voice'); seen.disconnect(); } }, { threshold: 0.4 });
      seen.observe(demo);
    } else play('voice');
  }

  /* ── copy buttons on code blocks ──────────────────────────────────────── */
  $$('.codeblock').forEach(function (block) {
    var pre = $('pre', block); if (!pre) return;
    var b = document.createElement('button'); b.type = 'button'; b.className = 'copy'; b.textContent = 'Copy'; b.setAttribute('aria-label', 'Copy code');
    b.addEventListener('click', function () {
      var text = pre.innerText.replace(/\n$/, '');
      var done = function () { b.textContent = 'Copied'; b.classList.add('done'); setTimeout(function () { b.textContent = 'Copy'; b.classList.remove('done'); }, 1600); };
      var fallback = function () { var ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.focus(); ta.select(); try { document.execCommand('copy'); done(); } catch (e) {} ta.remove(); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
      else fallback();
    });
    block.appendChild(b);
  });

  /* ── OS tabs (docs + download) ────────────────────────────────────────── */
  $$('.ostabs').forEach(function (group) {
    var tabs = $$('[role="tab"]', group), panels = $$('[role="tabpanel"]', group);
    function select(t) {
      tabs.forEach(function (x) { x.setAttribute('aria-selected', String(x === t)); x.tabIndex = x === t ? 0 : -1; });
      panels.forEach(function (p) { p.hidden = p.id !== t.getAttribute('aria-controls'); });
    }
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { select(t); });
      t.addEventListener('keydown', function (e) {
        var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0; if (!d) return;
        var n = tabs[(i + d + tabs.length) % tabs.length]; n.focus(); select(n);
      });
    });
    var want = os === 'mac' ? 'mac' : os === 'linux' ? 'linux' : 'windows';
    var pick = tabs.filter(function (t) { return t.getAttribute('data-os') === want; })[0] || tabs[0];
    if (pick) select(pick);
  });

  /* ── docs: search + active section + mobile menu ──────────────────────── */
  var side = $('.side');
  if (side) {
    var input = $('#doc-search'), items = $$('.side .groups a'), sections = $$('.prose section[id]');
    var sideToggle = $('.side-toggle', side);
    if (sideToggle) sideToggle.addEventListener('click', function () { var o = side.classList.toggle('open'); sideToggle.setAttribute('aria-expanded', String(o)); });
    items.forEach(function (a) { a.addEventListener('click', function () { if (window.innerWidth <= 1020) { side.classList.remove('open'); } }); });
    var index = sections.map(function (s) { return { id: s.id, text: s.innerText.toLowerCase() }; });
    if (input) input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase(), shown = 0;
      if (q.length > 1 && !side.classList.contains('open') && window.innerWidth <= 1020) side.classList.add('open');
      items.forEach(function (a) {
        var id = a.getAttribute('href').slice(1), hit = !q || (index.filter(function (s) { return s.id === id && s.text.indexOf(q) > -1; }).length > 0) || a.textContent.toLowerCase().indexOf(q) > -1;
        a.parentElement.hidden = !hit; if (hit) shown++;
      });
      $$('.side h5').forEach(function (h) {
        var ul = h.nextElementSibling, any = ul && $$('li', ul).some(function (li) { return !li.hidden; }); h.hidden = !any; if (ul) ul.hidden = !any;
      });
      var e = $('.side .empty'); if (e) e.hidden = shown > 0;
    });
    if ('IntersectionObserver' in window) {
      var act = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          items.forEach(function (a) { a.classList.toggle('active', a.getAttribute('href') === '#' + en.target.id); });
        });
      }, { rootMargin: '-90px 0px -65% 0px', threshold: 0 });
      sections.forEach(function (s) { act.observe(s); });
    }
  }

  /* ── download popup: pick your OS, then download ─────────────────────────
     Every [data-dl] button opens this. Without JavaScript the buttons still
     work as plain links. The Gemini key is NOT collected here — it is pasted
     into the app's own setup screen on first launch and stays on that computer. */
  var dlModal = null, dlLast = null, dlChoice = { os: null, arch: 'mac-arm' };
  var OS_META = {
    windows: { name: 'Windows', sub: 'Windows 10 & 11 · 64-bit', icon: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 5.5 10.5 4.4v7H3zM11.5 4.3 21 3v8.4h-9.5zM3 12.6h7.5v7L3 18.5zM11.5 12.6H21V21l-9.5-1.3z"/></svg>' },
    mac:     { name: 'macOS',   sub: 'Apple silicon & Intel',  icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z"/></svg>' },
    linux:   { name: 'Linux',   sub: '64-bit · Ubuntu 22.04+', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>' }
  };
  function dlKey() { return dlChoice.os === 'mac' ? dlChoice.arch : dlChoice.os; }
  function dlUrl() {
    var m = S.assets && S.assets[dlKey()];
    return repoOk && m ? repoUrl + '/releases/latest/download/' + m.file : (repoOk ? repoUrl + '/releases' : 'download.html');
  }
  function dlBuild() {
    var d = document.createElement('div'); d.className = 'dlm'; d.hidden = true;
    d.innerHTML =
      '<div class="dlm-back" data-close></div>' +
      '<div class="dlm-card" role="dialog" aria-modal="true" aria-labelledby="dlm-title">' +
        '<button class="dlm-x" type="button" data-close aria-label="Close"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12"/></svg></button>' +
        '<div class="dlm-head"><span class="orb" aria-hidden="true"></span><div><h3 id="dlm-title">Download JARVIS</h3><p>Choose your operating system</p></div></div>' +
        '<div class="dlm-os" role="radiogroup" aria-label="Operating system">' +
          ['windows', 'mac', 'linux'].map(function (k) {
            return '<button type="button" class="dlm-opt" role="radio" aria-checked="false" data-os="' + k + '">' + OS_META[k].icon + '<b>' + OS_META[k].name + '</b><span>' + OS_META[k].sub + '</span><i class="dlm-auto" hidden>Detected</i></button>';
          }).join('') +
        '</div>' +
        '<div class="dlm-arch" hidden><p>Which Mac do you have?</p><div><button type="button" class="dlm-chip" data-arch="mac-arm">Apple silicon (M1 or newer)</button><button type="button" class="dlm-chip" data-arch="mac-x64">Intel</button></div><small>Not sure? Apple menu → About This Mac.</small></div>' +
        '<a class="btn btn-primary btn-lg dlm-go" href="#" download><span data-go-label>Download</span></a>' +
        '<ol class="dlm-next"><li><b>Install it</b> and open JARVIS.</li><li>On the first-launch screen, <b>confirm your OS</b> and paste your free Gemini API key &mdash; <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener">get one here</a>.</li><li>Press <b>Initialise Systems</b>.</li></ol>' +
        '<p class="dlm-fine">Your key is typed into the app on your own computer &mdash; never on this website. <a data-releases href="#" rel="noopener">All releases</a></p>' +
      '</div>';
    document.body.appendChild(d);
    $$('[data-releases]', d).forEach(function (a) { a.href = repoUrl + '/releases'; });
    d.addEventListener('click', function (e) {
      if (e.target.closest('[data-close]')) return dlClose();
      var opt = e.target.closest('.dlm-opt'); if (opt) { dlChoice.os = opt.getAttribute('data-os'); return dlPaint(); }
      var chip = e.target.closest('.dlm-chip'); if (chip) { dlChoice.arch = chip.getAttribute('data-arch'); return dlPaint(); }
      if (e.target.closest('.dlm-go')) setTimeout(dlClose, 400);           // let the download start, then close
    });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') return dlClose();
      if (e.key !== 'Tab') return;                                          // keep focus inside the dialog
      var f = $$('button, a[href]', d).filter(function (x) { return x.offsetParent !== null; });
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    return d;
  }
  function dlPaint() {
    $$('.dlm-opt', dlModal).forEach(function (b) {
      var on = b.getAttribute('data-os') === dlChoice.os;
      b.setAttribute('aria-checked', String(on)); b.classList.toggle('on', on);
      $('.dlm-auto', b).hidden = b.getAttribute('data-os') !== (os === 'windows' || os === 'mac' || os === 'linux' ? os : '');
    });
    $('.dlm-arch', dlModal).hidden = dlChoice.os !== 'mac';
    $$('.dlm-chip', dlModal).forEach(function (c) { c.classList.toggle('on', c.getAttribute('data-arch') === dlChoice.arch); });
    var go = $('.dlm-go', dlModal), m = S.assets && S.assets[dlKey()];
    go.href = dlUrl();
    $('[data-go-label]', go).textContent = 'Download for ' + OS_META[dlChoice.os].name + (dlChoice.os === 'mac' ? (dlChoice.arch === 'mac-x64' ? ' (Intel)' : ' (Apple silicon)') : '');
    if (m) go.setAttribute('download', m.file);
  }
  function dlOpen(preKey, trigger) {
    if (!dlModal) dlModal = dlBuild();
    dlLast = trigger || document.activeElement;
    if (preKey && preKey !== 'auto') { dlChoice.os = preKey.indexOf('mac') === 0 ? 'mac' : preKey; if (preKey.indexOf('mac') === 0) dlChoice.arch = preKey; }
    else dlChoice.os = (os === 'windows' || os === 'mac' || os === 'linux') ? os : 'windows';
    if (dlChoice.os === 'mac' && preKey === 'auto') dlChoice.arch = macArch;
    dlPaint();
    dlModal.hidden = false; document.documentElement.classList.add('dlm-open');
    var pick = $('.dlm-opt.on', dlModal); if (pick) pick.focus();
  }
  function dlClose() {
    if (!dlModal) return;
    dlModal.hidden = true; document.documentElement.classList.remove('dlm-open');
    if (dlLast && dlLast.focus) dlLast.focus();
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('[data-dl]');
    if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button > 0) return;
    e.preventDefault(); dlOpen(a.getAttribute('data-dl'), a);
  });

  /* ── contact form ─────────────────────────────────────────────────────── */
  var form = $('#contact-form');
  if (form) {
    var msg = $('.form-msg', form), btn = $('button[type=submit]', form);
    var say = function (t, cls) { msg.textContent = t; msg.className = 'form-msg ' + (cls || ''); };
    form.addEventListener('submit', function (e) {
      e.preventDefault(); say('');
      var d = { name: form.name.value.trim(), email: form.email.value.trim(), topic: form.topic.value, message: form.message.value.trim() };
      $$('[aria-invalid]', form).forEach(function (x) { x.removeAttribute('aria-invalid'); });
      var bad = !d.name ? form.name : !/^[^@\s]+@[^@\s]+\.[^@\s.]{2,}$/.test(d.email) ? form.email : d.message.length < 10 ? form.message : null;
      if (bad) { bad.setAttribute('aria-invalid', 'true'); bad.focus(); say(bad === form.message ? 'Please write at least a sentence so we can help.' : bad === form.email ? 'Enter a valid email address.' : 'Enter your name.', 'err'); return; }
      if (form.website.value) { say('Thanks! We\u2019ll be in touch.', 'ok'); return; }       // honeypot: a bot filled it in
      var mailto = function () {
        location.href = 'mailto:' + S.email + '?subject=' + encodeURIComponent('[' + d.topic + '] from ' + d.name) + '&body=' + encodeURIComponent(d.message + '\n\n\u2014 ' + d.name + ' (' + d.email + ')');
        say('Your email app should open with the message ready to send. If it did not, write to ' + S.email + '.', 'ok');
      };
      if (!S.formEndpoint) { mailto(); return; }
      btn.disabled = true; btn.textContent = 'Sending…';
      fetch(S.formEndpoint, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(d) })
        .then(function (r) { if (!r.ok) throw new Error('bad status'); say('Thanks \u2014 your message is on its way. We usually reply within two days.', 'ok'); form.reset(); })
        .catch(function () { say('Could not send right now. Please email ' + S.email + ' instead.', 'err'); })
        .then(function () { btn.disabled = false; btn.textContent = 'Send message'; });
    });
  }
})();
