/* TapePhoto — analytics loader.
 *
 * THE ONLY PLACE THE GA4 ID LIVES. Every page loads this file from <head>;
 * to turn analytics on, create a GA4 property at analytics.google.com and put
 * its Measurement ID (looks like "G-XXXXXXXXXX") on the line below. Nothing
 * else needs to change anywhere on the site.
 *
 * While GA4_ID is empty this file is a deliberate no-op: no network request,
 * no cookie, no console noise. That keeps the site clean (and cookie-banner
 * free) until there is actually a property to report into.
 *
 * Conversion events are fired from main.js — see trackEvent() there. The one
 * that matters is `generate_lead`; mark it as a key event in GA4 once data
 * starts arriving.
 */
(function () {
    'use strict';

    var GA4_ID = 'G-0ZZHDP00H6'; // tapephoto.com property, created 2026-08-03

    window.TAPEPHOTO_GA4_ID = GA4_ID;

    if (!GA4_ID) {
        // No property yet. Define a harmless stub so main.js can call
        // window.gtag() unconditionally without feature-checking everywhere.
        window.gtag = window.gtag || function () {};
        return;
    }

    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    // ── Consent ─────────────────────────────────────────────────────────────
    // Same behaviour as netwebmedia.com (js/main.js "Cookie Consent Banner"): GA4 Consent Mode
    // v2, default denied until the visitor chooses, choice kept 365 days in the first-party
    // cookie nwm_consent = all | essential. No inline script or style: the banner is built with
    // the DOM API and styled by /consent.css, so the strict CSP stays untouched. GA4 always
    // loads; until the visitor accepts, every storage signal is denied (cookieless pings).
    var CK = 'nwm_consent';
    function readConsent() {
      var m = document.cookie.match(/(?:^|;\s*)nwm_consent=([^;]+)/);
      return m ? decodeURIComponent(m[1]) : null;
    }
    function writeConsent(v) {
      var d = new Date();
      d.setTime(d.getTime() + 365 * 24 * 60 * 60 * 1000);
      document.cookie = CK + '=' + encodeURIComponent(v) + ';expires=' + d.toUTCString() + ';path=/;SameSite=Lax';
    }
    function signals(v) {
      var g = v === 'all' ? 'granted' : 'denied';
      return { ad_storage: g, ad_user_data: g, ad_personalization: g, analytics_storage: g };
    }
    var isEs = /^es/i.test(document.documentElement.lang || '');
    var TXT = isEs ? {
      t: 'Cookies de analítica',
      b: 'Medimos visitas con Google Analytics. Sin cookies si no aceptas; con cookies solo si aceptas.',
      more: 'Política de privacidad',
      ok: 'Aceptar', no: 'Rechazar', url: '/privacidad.html#analytics'
    } : {
      t: 'Analytics cookies',
      b: 'We measure visits with Google Analytics: cookieless unless you accept.',
      more: 'Privacy policy',
      ok: 'Accept', no: 'Reject', url: '/privacy.html#analytics'
    };
    function mountBanner() {
      if (document.getElementById('consent-banner') || !document.body) return;
      if (!document.getElementById('consent-css')) {
        var css = document.createElement('link');
        css.id = 'consent-css'; css.rel = 'stylesheet'; css.href = '/consent.css?v=1';
        document.head.appendChild(css);
      }
      var box = document.createElement('div');
      box.id = 'consent-banner';
      box.setAttribute('role', 'dialog');
      box.setAttribute('aria-label', TXT.t);
      var p = document.createElement('p');
      p.className = 'consent-text';
      p.appendChild(document.createTextNode(TXT.b + ' '));
      var a = document.createElement('a');
      a.href = TXT.url; a.textContent = TXT.more;
      p.appendChild(a);
      var row = document.createElement('div');
      row.className = 'consent-actions';
      function btn(label, value) {
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'consent-btn'; b.textContent = label;
        b.addEventListener('click', function () {
          writeConsent(value);
          gtag('consent', 'update', signals(value));
          box.remove();
        });
        return b;
      }
      row.appendChild(btn(TXT.no, 'essential'));
      row.appendChild(btn(TXT.ok, 'all'));
      box.appendChild(p); box.appendChild(row);
      document.body.appendChild(box);
    }
    document.addEventListener('click', function (e) {
      var t = e.target && e.target.closest ? e.target.closest('[data-consent-open]') : null;
      if (t) { e.preventDefault(); mountBanner(); }
    });
    var saved = readConsent();
    var defaults = signals(saved);
    defaults.wait_for_update = 500;
    gtag('consent', 'default', defaults);
    if (!saved) {
      // Like netwebmedia.com: mount 1.5 s after DOMContentLoaded, so it never competes with first paint.
      var later = function () { setTimeout(mountBanner, 1500); };
      if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', later);
      else later();
    }

    window.gtag('js', new Date());
    // Chilean visitors: keep IP anonymisation on by default.
    window.gtag('config', GA4_ID, { anonymize_ip: true });

    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA4_ID);
    document.head.appendChild(s);
})();
