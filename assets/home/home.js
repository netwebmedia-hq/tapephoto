/* tapephoto.com homepage behaviour: per-device spans, the index drawer, frame
   jumps, the contact strip, the swing of the line, and the developer tray.
   The scroll-craft engine (scrollcraft.js) is copied verbatim and untouched;
   everything bespoke is here. CSP-safe: no inline script, only CSSOM writes. */
(function () {
  'use strict';

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var phone = window.matchMedia('(max-width: 860px)').matches;
  var root = document.documentElement;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var clamp = function (v, a, b) { return v < a ? a : v > b ? b : v; };
  var ss = function (a, b, v) { var t = clamp((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
  var r2 = function (v) { return Math.round(v * 100) / 100; };

  // Spans are authored per device before the engine reads them: a phone rail is
  // several screens wide, and with reduced motion the hero has nothing to travel.
  // shortcut: read once at load, so rotating across 860px keeps the first spans; fine for a homepage.
  var spans = { hero: phone ? 1.6 : 2, line: phone ? 4.2 : 3.2, tray: phone ? 4.8 : 3.8 };
  if (reduce) { spans.hero = 1.2; spans.line = 1.3; spans.tray = 3; }
  Object.keys(spans).forEach(function (k) {
    var el = $('[data-span-key="' + k + '"]');
    if (el) el.setAttribute('data-sc-span', String(spans[k]));
  });

  ScrollCraft.mount(document.body);

  var vw = function () { return root.clientWidth; };
  var vh = function () { return window.innerHeight; };
  var progress = function (act) {           // raw pinned progress, as the engine computes it
    var r = act.getBoundingClientRect();
    return clamp(-r.top / Math.max(r.height - vh(), 1), 0, 1);
  };

  // ------------------------------------------------------------ index drawer
  var toggle = $('.bar__index'), drawer = $('#index'), closeBtn = $('.index__close');
  function openIndex() {
    drawer.hidden = false;
    root.classList.add('index-open');
    toggle.setAttribute('aria-expanded', 'true');
    requestAnimationFrame(function () { drawer.classList.add('is-open'); });
    closeBtn.focus();
  }
  function closeIndex(restore) {
    drawer.classList.remove('is-open');
    root.classList.remove('index-open');
    toggle.setAttribute('aria-expanded', 'false');
    drawer.hidden = true;
    if (restore !== false) toggle.focus();
  }
  toggle.addEventListener('click', function () { if (drawer.hidden) openIndex(); else closeIndex(); });
  closeBtn.addEventListener('click', function () { closeIndex(); });
  document.addEventListener('keydown', function (e) {
    if (drawer.hidden) return;
    if (e.key === 'Escape') { e.preventDefault(); closeIndex(); return; }
    if (e.key !== 'Tab') return;                       // keep focus inside the dialog
    var f = $$('a[href], button', drawer);
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  // -------------------------------------------------------------- frame jumps
  // A frame on the line lives inside a sideways rail, and the developed print
  // only exists at the end of its act, so an anchor alone lands in the wrong place.
  function frameTop(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    var y = window.scrollY;
    if (id === 'fr-01') return 0;
    var act = el.closest('[data-sc-act="pan"]');
    if (act) {
      var rail = $('[data-sc-pan]', act);
      var over = rail.scrollWidth - vw();
      var extra = parseFloat(rail.getAttribute('data-sc-pan')) || 0;
      var x = el.offsetLeft + el.offsetWidth / 2 - vw() / 2;
      var p = over > 0 ? clamp(x / (over * (1 + extra)), 0, 1) : 0;
      var top = act.getBoundingClientRect().top + y;
      return top + p * (act.offsetHeight - vh());
    }
    if (id === 'fr-09') {
      var t = el.getBoundingClientRect().top + y;
      return t + 0.97 * (el.offsetHeight - vh());
    }
    return el.getBoundingClientRect().top + y - vh() * 0.12;
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[data-jump]');
    if (!a) return;
    var id = a.getAttribute('data-jump');
    var top = frameTop(id);
    if (top === null) return;
    e.preventDefault();
    if (!drawer.hidden) closeIndex(false);
    window.scrollTo({ top: top, behavior: reduce ? 'auto' : 'smooth' });
    var el = document.getElementById(id);
    if (el) el.focus({ preventScroll: true });
    history.replaceState(null, '', '#' + id);
  });

  // Keyboard focus inside the rail or the tray label: the engine cannot centre a
  // control in a sideways or pinned act, so park the act where that frame shows.
  document.addEventListener('focusin', function (e) {
    var item = e.target.closest && e.target.closest('.line-rail .item, #fr-09 .label');
    if (!item) return;
    var id = item.id || 'fr-09';
    var top = frameTop(id);
    if (top === null) return;
    // The browser's own focus scroll can start after this event; land again a frame later to cancel it.
    var park = function () { if (Math.abs(window.scrollY - top) > 4) window.scrollTo({ top: top, behavior: 'instant' }); };
    park();
    requestAnimationFrame(function () { requestAnimationFrame(park); });
  });

  // ------------------------------------------------------------ the strip
  // Frames print positive once seen; the current one is outlined.
  var strip = $$('.strip a').map(function (a) {
    var id = a.getAttribute('data-jump');
    return { a: a, id: id, el: document.getElementById(id), seen: false };
  });
  var hero = $('#fr-01'), line = $('#work'), trayAct = $('#fr-09');
  function onCentre(r) { return r.top < vh() * 0.62 && r.bottom > vh() * 0.38; }
  function frameState(f) {
    var r = f.el.getBoundingClientRect();
    if (f.id === 'fr-01') { var hr = hero.getBoundingClientRect(); return hr.top <= 1 && hr.bottom > vh() * 0.5 ? 2 : 0; }
    if (f.id === 'fr-09') {
      var tr = trayAct.getBoundingClientRect();
      if (!(tr.top <= vh() * 0.5 && tr.bottom > vh() * 0.5)) return 0;
      return progress(trayAct) > 0.8 ? 2 : 1;          // only seen once it has developed
    }
    if (f.el.closest('.line-rail')) {
      var lr = line.getBoundingClientRect();
      if (!(lr.top <= vh() * 0.5 && lr.bottom > vh() * 0.5)) return 0;
      return r.left < vw() * 0.66 && r.right > vw() * 0.34 ? 2 : 0;
    }
    return onCentre(r) ? 2 : 0;
  }
  var stripOn = strip.length && getComputedStyle($('.strip')).display !== 'none';
  function updateStrip() {
    var current = null;
    strip.forEach(function (f) {
      var s = frameState(f);
      if (s && !current) current = f;
      if (s === 2 && !f.seen) { f.seen = true; f.a.classList.add('is-seen'); }
    });
    strip.forEach(function (f) {
      var on = f === current;
      if (on !== f.a.classList.contains('is-current')) {
        f.a.classList.toggle('is-current', on);
        if (on) f.a.setAttribute('aria-current', 'true'); else f.a.removeAttribute('aria-current');
      }
    });
  }

  // ------------------------------------------------------------ the line
  // Prints hang from a top edge, so when the line moves they lag and swing.
  var rail = $('.line-rail');
  var prints = $$('.line-rail .item .print').map(function (el, i) {
    return { el: el, a: 0, v: 0, k: 0.07 + (i % 3) * 0.012, last: null };
  });
  var railX = null;
  function swing() {
    var lr = line.getBoundingClientRect();
    if (lr.bottom < 0 || lr.top > vh()) { railX = null; return; }
    var x = rail.getBoundingClientRect().left;
    var dx = railX === null ? 0 : x - railX;
    railX = x;
    var target = clamp(dx * 0.22, -4.5, 4.5);
    prints.forEach(function (p) {
      p.v += (target - p.a) * p.k;
      p.v *= 0.84;
      p.a += p.v;
      var out = Math.abs(p.a) < 0.01 ? 0 : r2(p.a);
      if (out !== p.last) { p.el.style.setProperty('--swing', String(out)); p.last = out; }
    });
  }

  // ------------------------------------------------------------ the tray
  // Hush (0 to .14), the sheet goes in (.14 to .30), develop (.30 to .70):
  // brightness falls from paper-white so the darkest tones arrive first, the
  // way a print comes up in the developer. Lights on (.70), colour (.73 to .83),
  // the print lifts to full bleed (.78 to .95), its label holds to the end.
  var stage = $('.trayroom'), tray = $('.tray', stage), sheet = $('.sheet', stage), img = $('.sheet__img', stage);
  var lastY = window.scrollY, agit = 0, trayState = '';
  function develop() {
    var tr = trayAct.getBoundingClientRect();
    if (tr.bottom < -vh() || tr.top > vh() * 2) return;
    var p = progress(trayAct);
    var drop = reduce ? 1 : ss(0.14, 0.30, p);
    var dev = ss(0.30, 0.70, p);
    var on = ss(0.70, 0.745, p);
    var colour = ss(0.73, 0.83, p);
    var lift = reduce ? 0 : ss(0.78, 0.95, p);
    // Paper value is linear in the print's tone, clipped at white: s0 at black,
    // hi at white. s0 starts above 1 (blank sheet) and falls first, so shadows
    // come up before midtones; hi stays clipped until late. Done as CSS
    // contrast() then brightness(), because brightness() alone keeps pure black.
    var s0 = 1.15 * Math.pow(1 - dev, 1.6), hi = 1 + 1.4 * Math.pow(1 - dev, 1.2);
    var b = s0 + hi, c = (hi - s0) / (hi + s0);
    var shaking = !reduce && p > 0.14 && p < 0.74;
    var a = shaking ? clamp(agit / 40, -1, 1) : 0;

    img.style.filter = 'grayscale(' + (1 - colour).toFixed(3) + ') contrast(' + c.toFixed(4) + ') brightness(' + b.toFixed(4) + ')';
    var cover = Math.max(vw() / Math.max(img.offsetWidth, 1), vh() / Math.max(img.offsetHeight, 1)) * 1.03;
    var s = 1 + (cover - 1) * lift;
    // Full bleed crops a 3:2 print hard on a phone; keep the car (about 62% across) in frame.
    var spare = Math.max(img.offsetWidth * s - vw(), 0) / 2;
    var fx = clamp((0.5 - 0.62) * img.offsetWidth * s, -spare, spare) * lift;
    var y = -(1 - drop) * vh() * 0.85;
    var rot = (reduce ? 0 : -7 * (1 - drop) - 1.3 * (1 - lift)) + a * 0.9;
    sheet.style.transform = 'translate3d(' + (a * 6 + fx).toFixed(1) + 'px,' + y.toFixed(1) + 'px,0) rotate(' + rot.toFixed(2) + 'deg) scale(' + s.toFixed(4) + ')';
    sheet.style.opacity = reduce ? '1' : ss(0.13, 0.17, p).toFixed(3);

    stage.style.setProperty('--tilt3d', (reduce ? 18 : 24 * (1 - lift)).toFixed(2) + 'deg');
    stage.style.setProperty('--safe', (0.9 * (1 - on)).toFixed(3));
    stage.style.setProperty('--day', on.toFixed(3));
    stage.style.setProperty('--tray-o', (1 - lift).toFixed(3));
    stage.style.setProperty('--scrim-o', (reduce ? on : lift).toFixed(3));
    // The label rides the stage when it un-pins; fade it before it reaches the bar.
    var exit = clamp((vh() - tr.bottom) / vh(), 0, 1);
    stage.style.setProperty('--label-o', (1 - ss(0.05, 0.4, exit)).toFixed(3));
    stage.style.setProperty('--slosh', (50 + a * 30).toFixed(1) + '%');
    var rp = ss(0.27, 0.40, p);
    stage.style.setProperty('--ripple-s', (0.6 + rp * 0.9).toFixed(3));
    stage.style.setProperty('--ripple-o', reduce ? '0' : ((ss(0.27, 0.29, p) - ss(0.29, 0.40, p)) * 0.6).toFixed(3));

    // What actually paints, rounded, for the verification harness.
    var state = [drop, dev, on, colour, lift].map(r2).join(',');
    if (state !== trayState) { stage.setAttribute('data-sc-verify-state', state); trayState = state; }
  }

  // ------------------------------------------------------------ hero state
  // The hero's planes move in CSS from --sc-p; publish their rendered offset.
  var heroStage = $('.room', hero), heroState = '';
  function heroVerify() {
    var p = progress(hero);
    var s = String(Math.round(p * 0.3 * vw())) + ',' + Math.round(p * 0.24 * vh());
    if (s !== heroState) { heroStage.setAttribute('data-sc-verify-state', s); heroState = s; }
  }

  // ------------------------------------------------------------ one loop
  function frame() {
    var y = window.scrollY;
    agit = agit * 0.86 + (y - lastY) * 0.14;
    lastY = y;
    if (!reduce) swing();
    develop();
    heroVerify();
    if (stripOn) updateStrip();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
