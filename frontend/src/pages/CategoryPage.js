import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Seo } from "@/components/Seo";
import { PostCard } from "@/components/PostCard";
import { api, CATEGORIES } from "@/lib/api";
import { pillarAccent, withAlpha, PillarMotif, pillarMascot, PILLAR_MASCOT_ALTS, PILLAR_LORE } from "@/lib/pillars";

export default function CategoryPage() {
  const { slug } = useParams();
  const category = CATEGORIES.find((c) => c.slug === slug);
  const [posts, setPosts] = useState(null);

  useEffect(() => {
    setPosts(null);
    api.get("/posts", { params: { category: slug } })
      .then((res) => setPosts(res.data.posts))
      .catch(() => setPosts([]));
  }, [slug]);

  if (!category) {
    return (
      <div className="container-editorial py-24 text-center">
        <h1 className="font-serif text-3xl font-semibold mb-3">Category not found</h1>
        <Link to="/" className="editorial-link text-accent">Back home</Link>
      </div>
    );
  }

  const accent = pillarAccent(slug);
  const lore = PILLAR_LORE[slug];

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="category-page">
      <Seo title={category.label} description={category.description} path={`/category/${slug}`} />
      <div
        className="relative overflow-hidden rounded-2xl border px-6 sm:px-10 py-8 sm:py-10"
        style={{ borderColor: withAlpha(accent, 0.35), backgroundColor: withAlpha(accent, 0.07) }}
        data-testid="category-header-banner"
      >
        <div className="absolute inset-y-0 right-0 w-3/4 sm:w-1/2 pointer-events-none" style={{ color: accent, opacity: 0.16 }}>
          <PillarMotif category={slug} className="h-full w-full" />
        </div>
        <div className="relative flex items-center gap-6 sm:gap-10">
          <div className="min-w-0 flex-1">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em]" style={{ color: accent }}>
              Pillar{lore?.name ? ` · ${lore.name}` : ""}
            </span>
            <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3 leading-tight" data-testid="category-title">{category.label}</h1>
            <p className="text-muted-foreground text-lg mt-4 max-w-2xl leading-relaxed">{category.description}</p>
            <div className="h-1 w-16 rounded-full mt-5" style={{ backgroundColor: accent }} aria-hidden />
          </div>
          <img
            src={pillarMascot(slug)}
            alt={PILLAR_MASCOT_ALTS[slug]}
            className="h-20 w-20 sm:h-32 sm:w-32 lg:h-40 lg:w-40 rounded-full object-cover shrink-0 shadow-lg"
            style={{ border: `3px solid ${withAlpha(accent, 0.55)}` }}
            loading="lazy"
            data-testid="category-mascot"
          />
        </div>
      </div>
      <Separator className="my-10" />
      {posts === null ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-80 rounded-xl" />)}</div>
      ) : posts.length === 0 ? (
        <p className="text-muted-foreground py-12" data-testid="category-empty">No posts in this pillar yet. Check back soon.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" data-testid="category-posts-grid">
          {posts.map((p) => <PostCard key={p.id} post={p} />)}
        </div>
      )}
    </div>
  );
}
