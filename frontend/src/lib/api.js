import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;
export const SITE_URL = BACKEND_URL;
export const SITE_NAME = "The Trading Narrative";

export const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ttn_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const CATEGORIES = [
  {
    slug: "tech-business",
    label: "Tech & AI",
    description:
      "Operator-grade insights on AI, technology, and the business models being built on them.",
  },
  {
    slug: "finance",
    label: "Business & Finance",
    description:
      "Markets, investing, and business strategy, minus the noise. Portfolios, macro, and the psychology of money.",
  },
  {
    slug: "lifestyle",
    label: "Personal Growth",
    description:
      "Focus, habits, and the systems behind a deliberately designed life.",
  },
  {
    slug: "travel",
    label: "Travel",
    description:
      "Slow travel, remote work, and seeing the world without wrecking your budget or your career.",
  },
];

export const categoryLabel = (slug) =>
  CATEGORIES.find((c) => c.slug === slug)?.label || slug;

export const trackEvent = (event, path = "", meta = {}) => {
  api.post("/analytics/track", { event, path, meta }).catch(() => {});
};

export const formatDate = (iso) => {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return "";
  }
};

export const detectIndia = () => {
  try {
    if (Intl.DateTimeFormat().resolvedOptions().timeZone === "Asia/Kolkata") return true;
    if ((navigator.language || "").toLowerCase().endsWith("-in")) return true;
  } catch { /* ignore */ }
  return false;
};

export const getPreferredCurrency = () => {
  const stored = localStorage.getItem("ttn_currency");
  if (stored === "usd" || stored === "inr") return stored;
  return detectIndia() ? "inr" : "usd";
};

export const setPreferredCurrency = (c) => localStorage.setItem("ttn_currency", c);

export const formatINR = (n) => `₹${Number(n).toLocaleString("en-IN")}`;
