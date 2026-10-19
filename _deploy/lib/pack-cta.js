// _deploy/lib/pack-cta.js
// One place for the "Pack Listing" (Airbnb / short-term rental) CTA that blog posts
// carry. Used by blog-publish.js for new posts and by backfill runs for old ones.
// No prices here or anywhere on public pages: the pack is quote-based.

const PACK_PAGE = 'fotos-airbnb-la-serena.html';

// A post gets the CTA when its tag is Turismo or Inmobiliaria, or its slug or title
// names the topic (Airbnb, temporada, cabañas, hoteles, alojamiento, corredores, propiedades).
// Restaurants share the Turismo tag but their readers do not rent by the season.
const TAGS = new Set(['Turismo', 'Inmobiliaria']);
const SLUG_RE = /airbnb|temporada|cabana|hotel|alojamiento|turis|corredor|propiedad|inmobiliari|glamping|casas?[- ]de[- ]playa/;
const SKIP_RE = /restaurante/;

// Titles carry accents, slugs do not: compare accent-free, lower-case text.
const plain = (t) => String(t || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

function wantsPackCta({ slug, tag, title }) {
  if (SKIP_RE.test(slug)) return false;
  return TAGS.has(tag) || SLUG_RE.test(plain(slug + ' ' + title));
}

// Blog posts live one level down, hence ../ ; same indentation as .article-cta.
function packCtaHtml() {
  return `            <div class="article-cta">
                <p class="article-cta-label">&iquest;Arriendas por temporada? Pack Listing: fotos + reel para tu aviso antes del verano</p>
                <div class="cta-row">
                    <a class="btn-outline" href="../${PACK_PAGE}">Ver el Pack Listing &rarr;</a>
                </div>
            </div>

`;
}

module.exports = { PACK_PAGE, wantsPackCta, packCtaHtml };
