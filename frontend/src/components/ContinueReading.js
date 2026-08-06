import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";

export const getReadingProgressMap = () => {
  try {
    return JSON.parse(localStorage.getItem("ttn_progress") || "{}");
  } catch {
    return {};
  }
};

export const ContinueReading = () => {
  const [items, setItems] = useState(null);

  useEffect(() => {
    const map = getReadingProgressMap();
    const entries = Object.entries(map)
      .filter(([, v]) => v.p > 0.03 && v.p < 0.95)
      .sort((a, b) => (b[1].t || 0) - (a[1].t || 0))
      .slice(0, 4);
    if (entries.length === 0) {
      setItems([]);
      return;
    }
    const slugs = entries.map(([slug]) => slug);
    api.get("/posts", { params: { slugs: slugs.join(",") } })
      .then((res) => {
        const bySlug = Object.fromEntries(res.data.posts.map((p) => [p.slug, p]));
        setItems(
          entries
            .filter(([slug]) => bySlug[slug])
            .map(([slug, v]) => ({ post: bySlug[slug], progress: v.p }))
        );
      })
      .catch(() => setItems([]));
  }, []);

  if (!items || items.length === 0) return null;

  return (
    <section className="container-editorial py-6 sm:py-8" data-testid="continue-reading-section">
      <span className="section-label">Pick up where you left off</span>
      <h2 className="font-serif text-2xl sm:text-3xl font-semibold mt-2 mb-6">Continue reading</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="continue-reading-grid">
        {items.map(({ post, progress }) => (
          <Link
            key={post.id}
            to={`/post/${post.slug}`}
            className="group bg-card border border-border rounded-xl p-4 flex gap-3 items-center hover:border-foreground/25 transition-colors"
            data-testid="continue-reading-card"
          >
            <div className="card-img-zoom overflow-hidden rounded-lg w-16 h-16 shrink-0">
              <img src={post.cover_image} alt={post.title} loading="lazy" className="w-full h-full object-cover" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="font-serif text-sm font-semibold leading-snug line-clamp-2 group-hover:text-accent transition-colors">
                {post.title}
              </h3>
              <div className="mt-2 h-1 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-accent rounded-full" style={{ width: `${Math.round(progress * 100)}%` }} />
              </div>
              <div className="text-[10px] font-mono text-muted-foreground mt-1">{Math.round(progress * 100)}% read</div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
};
