import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;
export const SITE_URL = BACKEND_URL;
export const SITE_NAME = "The Trading Narrative";

// Session auth rides in a secure httpOnly cookie (ttn_session) — set/cleared by the
// backend; withCredentials makes the browser attach it to every API call.
export const api = axios.create({ baseURL: API, withCredentials: true });

// Legacy migration shim: sessions created before the cookie upgrade stored a JWT in
// localStorage. Keep sending it as a Bearer header until AuthContext exchanges it
// for the httpOnly cookie (via /auth/cookie-sync) and deletes it.
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
    slug: "delivery",
    label: "Delivery & Systems",
    description:
      "The unglamorous systems that let large programmes run on time and under budget, governance, delivery, and the mechanics of execution.",
  },
];

export const categoryLabel = (slug) =>
  CATEGORIES.find((c) => c.slug === slug)?.label || slug;

const getSessionId = () => {
  try {
    let sid = sessionStorage.getItem("ttn_sid");
    if (!sid) {
      sid = (crypto.randomUUID && crypto.randomUUID()) || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      sessionStorage.setItem("ttn_sid", sid);
    }
    return sid;
  } catch {
    return null;
  }
};

export const trackEvent = (event, path = "", meta = {}) => {
  try {
    // Traffic-source attribution: tag the first pageview of each browser session
    if (event === "pageview" && !sessionStorage.getItem("ttn_visit_tracked")) {
      sessionStorage.setItem("ttn_visit_tracked", "1");
      meta = { ...meta, first_visit: true, referrer: document.referrer || "" };
      const params = new URLSearchParams(window.location.search);
      ["utm_source", "utm_medium", "utm_campaign"].forEach((k) => {
        const v = params.get(k);
        if (v) meta[k] = v;
      });
    }
  } catch { /* sessionStorage unavailable, track without attribution */ }
  api.post("/analytics/track", { event, path, meta, sid: getSessionId() }).catch(() => {});
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
