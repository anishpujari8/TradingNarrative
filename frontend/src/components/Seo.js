import { Helmet } from "react-helmet-async";
import { SITE_NAME, SITE_URL } from "@/lib/api";

export const Seo = ({ title, description, image, path = "", type = "website" }) => {
  const fullTitle = title ? `${title} — ${SITE_NAME}` : `${SITE_NAME} — Sharp narratives on markets, tech & living well`;
  const desc =
    description ||
    "A publication on technology & AI, business and financial mechanics, delivery systems, and personal growth — from inside commodity trading floors.";
  const url = `${SITE_URL}${path}`;
  const img =
    image ||
    "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&q=80&auto=format&fit=crop";
  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={desc} />
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
    </Helmet>
  );
};
