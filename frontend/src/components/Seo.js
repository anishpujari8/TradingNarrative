import { useEffect } from "react";
import { Helmet } from "react-helmet-async";
import { SITE_NAME, SITE_URL } from "@/lib/api";

// Site-wide default meta. Head terms: commodity trading, energy markets, trading
// technology, ETRM, market risk (+ freight / weekly briefing / newsletter).
const DEFAULT_TAGLINE = "Commodity Trading & Tech Insights";
const DEFAULT_DESC =
  "The Trading Narrative — commodity trading and tech insights: energy markets, trading technology, " +
  "ETRM systems, market risk, freight and shipping, plus a weekly briefing newsletter.";
const DEFAULT_KEYWORDS =
  "commodity trading, energy markets, trading technology, ETRM, market risk, trading narrative, " +
  "freight, shipping industry, weekly briefing, newsletter, business and finance, CTRM";

// Dynamic per-essay meta description: excerpt first, else the opening paragraphs,
// normalized and trimmed to ~160 chars at a word boundary.
export const metaDescription = (post, limit = 160) => {
  let text = (post?.excerpt || "").trim();
  if (!text) {
    const parts = [];
    for (const b of post?.content_blocks || []) {
      const s = (b || "").trim();
      if (!s || s.startsWith("#") || s.startsWith("![")) continue; // skip headings / images
      parts.push(s);
      if (parts.join(" ").length >= limit * 2) break;
    }
    text = parts.join(" ");
  }
  text = text.replace(/\s+/g, " ").trim();
  if (text.length <= limit) return text;
  const cut = text.slice(0, limit).split(" ").slice(0, -1).join(" ").replace(/[ ,;:.]+$/, "");
  return `${cut}…`;
};

export const Seo = ({ title, description, image, path = "", type = "website", keywords, jsonLd }) => {
  // The static meta tags in index.html are marked data-rh="true" as crawler fallbacks.
  // Helmet v3 renders its own tags WITHOUT that attribute, so once React is live we
  // drop the static ones to avoid duplicate/conflicting descriptions.
  useEffect(() => {
    document.querySelectorAll("head meta[data-rh]").forEach((el) => el.remove());
  }, []);

  const fullTitle = title ? `${title} · ${SITE_NAME}` : `${SITE_NAME} | ${DEFAULT_TAGLINE}`;
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
