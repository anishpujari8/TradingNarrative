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
    label: "Tech & Business",
    description:
      "Operator-grade insights on technology, startups, and the business models shaping the next decade.",
  },
  {
    slug: "finance",
    label: "Finance",
    description:
      "Personal finance and investing, minus the noise. Markets, portfolios, and the psychology of money.",
  },
  {
    slug: "lifestyle",
    label: "Lifestyle",
    description:
      "Personal growth, focus, and the systems behind a deliberately designed life.",
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
