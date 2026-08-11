import { useEffect } from "react";
import { Helmet } from "react-helmet-async";
import { SITE_NAME, SITE_URL } from "@/lib/api";

// Site-wide default meta, tuned for the head terms readers search for:
// trading, freight, business and finance, narrative, weekly briefing, newsletter.
const DEFAULT_TAGLINE = "Trading, Freight & Business and Finance Newsletter";
const DEFAULT_DESC =
  "The Trading Narrative — sharp essays and a weekly briefing newsletter on commodity trading, " +
  "freight and shipping markets, business and finance mechanics, trading technology and AI.";
const DEFAULT_KEYWORDS =
  "trading narrative, trading, freight, business and finance, weekly briefing, newsletter, " +
  "commodity trading, shipping industry, markets, ETRM, CTRM";

export const Seo = ({ title, description, image, path = "", type = "website", keywords, jsonLd }) => {
  // The static meta tags in index.html are marked data-rh="true" as crawler fallbacks.
  // Helmet v3 renders its own tags WITHOUT that attribute, so once React is live we
  // drop the static ones to avoid duplicate/conflicting descriptions.
  useEffect(() => {
    document.querySelectorAll("head meta[data-rh]").forEach((el) => el.remove());
  }, []);

  const fullTitle = title ? `${title} · ${SITE_NAME}` : `${SITE_NAME} · ${DEFAULT_TAGLINE}`;
  const desc = description || DEFAULT_DESC;
  const url = `${SITE_URL}${path}`;
  const img =
    image ||
    "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&q=80&auto=format&fit=crop";
  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={desc} />
      <meta name="keywords" content={keywords || DEFAULT_KEYWORDS} />
      <link rel="canonical" href={url} />
      <meta property="og:site_name" content={SITE_NAME} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={desc} />
      <meta property="og:image" content={img} />
      <meta property="og:url" content={url} />
      <meta property="og:type" content={type} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={desc} />
      <meta name="twitter:image" content={img} />
      {jsonLd && <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>}
    </Helmet>
  );
};
