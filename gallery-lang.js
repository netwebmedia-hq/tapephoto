/* Gallery pages carry Spanish and English text on the same URL (built by
 * _deploy/galleries/build-galleries.py). This file picks which one shows:
 *   1. the visitor's own ES / EN toggle choice (kept in localStorage),
 *   2. else the choice already made this visit (sessionStorage),
 *   3. else the language of the page they came from (Spanish page -> es, /en/ page -> en),
 *   4. else the browser language: "es*" -> es, anything else -> en.
 * It runs from <head>, before first paint, so <html lang> is right immediately and CSS (.bi)
 * hides the other language. No inline script, so the strict CSP stays untouched. */
(function () {
    'use strict';
    var KEY = 'tp_lang';
    var html = document.documentElement;
    function read(store, key) { try { return window[store].getItem(key); } catch (e) { return null; } }
    function write(store, key, val) { try { window[store].setItem(key, val); } catch (e) { /* private mode */ } }

    var ES_PAGE = /^\/(?:$|index\.html|servicios|contacto|licencias|impresiones|sobre-mi|privacidad|terminos|fotografia-|fotos-|sesion-fotos|checklist-)/;
    var EN_PAGE = /^\/(?:en\/|services\.html|contact\.html|licensing\.html|prints\.html|about\.html|privacy\.html|terms\.html)/;

    function fromReferrer() {
        try {
            if (!document.referrer) return null;
            var r = new URL(document.referrer);
            if (r.origin !== location.origin) return null;
            if (EN_PAGE.test(r.pathname)) return 'en';
            if (ES_PAGE.test(r.pathname)) return 'es';
        } catch (e) { /* bad referrer */ }
        return null;
    }

    function pick() {
        var saved = read('localStorage', KEY) || read('sessionStorage', KEY);
        if (saved === 'es' || saved === 'en') return saved;
        var ref = fromReferrer();
        if (ref) { write('sessionStorage', KEY, ref); return ref; }
        return /^es/i.test(navigator.language || '') ? 'es' : 'en';
    }

    function apply(lang) {
        html.setAttribute('lang', lang);
        if (!html.hasAttribute('data-title-en')) html.setAttribute('data-title-en', document.title);
        var es = html.getAttribute('data-title-es');
        document.title = lang === 'es' && es ? es : html.getAttribute('data-title-en');
        if (!document.body) return;
        var btns = document.querySelectorAll('[data-lang-set]');
        for (var i = 0; i < btns.length; i++) {
            btns[i].setAttribute('aria-pressed', btns[i].getAttribute('data-lang-set') === lang ? 'true' : 'false');
        }
        var labelled = document.querySelectorAll('[data-aria-es]');
        for (var j = 0; j < labelled.length; j++) {
            var el = labelled[j];
            if (!el.hasAttribute('data-aria-en')) el.setAttribute('data-aria-en', el.getAttribute('aria-label') || '');
            el.setAttribute('aria-label', el.getAttribute(lang === 'es' ? 'data-aria-es' : 'data-aria-en'));
        }
        var inputs = document.querySelectorAll('[data-placeholder-es]');
        for (var k = 0; k < inputs.length; k++) {
            if (!inputs[k].hasAttribute('data-placeholder-en')) inputs[k].setAttribute('data-placeholder-en', inputs[k].getAttribute('placeholder') || '');
            inputs[k].setAttribute('placeholder', inputs[k].getAttribute(lang === 'es' ? 'data-placeholder-es' : 'data-placeholder-en'));
        }
        var status = document.getElementById('gallery-search-status');
        if (status) status.textContent = '';
        var input = document.getElementById('gallery-search');
        if (input && input.value) input.dispatchEvent(new Event('input'));
    }

    apply(pick());
    document.addEventListener('DOMContentLoaded', function () { apply(html.getAttribute('lang')); });
    document.addEventListener('click', function (e) {
        var b = e.target && e.target.closest ? e.target.closest('[data-lang-set]') : null;
        if (!b) return;
        if (b.tagName === 'A') e.preventDefault();
        var lang = b.getAttribute('data-lang-set') === 'es' ? 'es' : 'en';
        write('localStorage', KEY, lang);
        apply(lang);
    });
}());
