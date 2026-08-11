import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Lock, Clock, ArrowRight, Zap } from "lucide-react";
import { Seo } from "@/components/Seo";
import { PostCard } from "@/components/PostCard";
import { NewsletterForm } from "@/components/NewsletterForm";
import { api, CATEGORIES, formatDate } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ContinueReading } from "@/components/ContinueReading";

const fadeUp = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.32, ease: [0.2, 0.8, 0.2, 1] },
};

export default function HomePage() {
  const { user, loading: authLoading } = useAuth();
  const [posts, setPosts] = useState(null);
  const [featured, setFeatured] = useState(null);
  const [filter, setFilter] = useState("all");
  const [recs, setRecs] = useState(null);
  const [promo, setPromo] = useState(null); // early supporter spots {limit, taken, left}

  useEffect(() => {
    api.get("/early-supporters").then((res) => setPromo(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (authLoading) return;
    let slugs = [];
    try {
      slugs = JSON.parse(localStorage.getItem("ttn_read_history") || "[]").map((h) => h.slug);
    } catch { /* ignore */ }
    if (slugs.length === 0 && !user) { setRecs({ posts: [], based_on: [] }); return; }
    api.get("/recommendations", { params: { slugs: slugs.join(","), limit: 3 } })
      .then((res) => setRecs(res.data))
      .catch(() => setRecs({ posts: [], based_on: [] }));
  }, [user, authLoading]);

  useEffect(() => {
    api.get("/posts").then((res) => {
      const all = res.data.posts;
      setPosts(all);
      setFeatured(all.find((p) => p.featured) || all[0]);
    }).catch(() => setPosts([]));
  }, []);

  const filtered = posts
    ? filter === "all"
      ? posts
      : posts.filter((p) => p.category === filter)
    : [];

  const latest = posts ? posts.filter((p) => p.slug !== featured?.slug).slice(0, 4) : [];

  return (
    <div data-testid="home-page">
      <Seo path="/" />

      {/* EARLY SUPPORTER PROMO, signup urgency while first-50 spots remain */}
      {promo && promo.left > 0 && !user?.early_supporter && !user?.is_premium && (
        <div className="bg-accent text-accent-foreground" data-testid="early-supporter-banner">
          <Link
            to="/auth"
            className="container-editorial flex items-center justify-center gap-2 py-2.5 text-sm hover:opacity-90 transition-opacity"
            data-testid="early-supporter-banner-link"
          >
            <Zap className="h-3.5 w-3.5 shrink-0" />
            <span className="truncate">
              Early supporter offer, <strong data-testid="early-supporter-count">{promo.left} of {promo.limit}</strong> spots
              left · first 5 essays free for early readers
            </span>
            <span className="hidden sm:inline-flex items-center gap-1 font-medium underline underline-offset-4 shrink-0">
              Claim yours <ArrowRight className="h-3.5 w-3.5" />
            </span>
          </Link>
        </div>
      )}

      {/* HERO */}
      <section
        className="relative"
        style={{
          backgroundImage:
            "radial-gradient(600px circle at 15% 0%, hsla(168,52%,34%,0.08), transparent 55%)",
        }}
      >
        <div className="container-editorial py-14 sm:py-20 grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center">
          <motion.div {...fadeUp} className="lg:col-span-6">
            <span className="section-label mb-5 inline-flex" data-testid="hero-label">
              A premium newsletter & magazine
            </span>
            <h1 className="font-serif text-4xl sm:text-5xl lg:text-6xl font-semibold leading-[1.05] mt-4" data-testid="hero-headline">
              Sharp narratives on money, technology, and a life well designed.
            </h1>
            <p className="text-muted-foreground text-base md:text-lg mt-5 max-w-lg">
              Essays on technology & AI, business and financial mechanics, delivery systems,
              and personal growth, written like a letter from a colleague who does the homework.
            </p>
            <div className="mt-7 max-w-md">
              <NewsletterForm source="hero" testId="hero-newsletter-form" />
              <p className="text-xs text-muted-foreground mt-2 font-mono">
                Free forever. Premium if you want everything.
              </p>
            </div>
          </motion.div>

          {featured ? (
            <motion.div {...fadeUp} transition={{ ...fadeUp.transition, delay: 0.1 }} className="lg:col-span-6">
              <Link to={`/post/${featured.slug}`} className="group block" data-testid="featured-post-card">
                <div className="relative card-img-zoom overflow-hidden rounded-2xl border border-border shadow-[var(--shadow-float)]">
                  <div className="aspect-[16/10]">
                    <img src={featured.cover_image} alt={featured.title} className="w-full h-full object-cover" />
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/20 to-transparent" />
                  <div className="absolute bottom-0 p-6 sm:p-8 text-white">
                    <div className="flex items-center gap-2 mb-3">
                      <Badge className="bg-accent text-accent-foreground hover:bg-accent font-mono text-[10px] uppercase tracking-wider">Featured</Badge>
                      {featured.tier === "premium" && (
                        <Badge className="bg-white/15 text-white border-white/30 hover:bg-white/15 gap-1"><Lock className="h-3 w-3" /> Premium</Badge>
                      )}
                    </div>
                    <h2 className="font-serif text-2xl sm:text-3xl font-semibold leading-snug group-hover:underline decoration-accent underline-offset-4">
                      {featured.title}
                    </h2>
                    <div className="flex items-center gap-3 mt-3 text-xs text-white/70 font-mono">
                      <span>{formatDate(featured.published_at)}</span>
                      <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" /> {featured.read_time} min</span>
                    </div>
                  </div>
                </div>
              </Link>
            </motion.div>
          ) : (
            <div className="lg:col-span-6"><Skeleton className="aspect-[16/10] rounded-2xl" /></div>
          )}
        </div>
        <div className="container-editorial"><Separator /></div>
      </section>

      {/* LATEST LIST */}
      <section className="container-editorial py-12 sm:py-16">
        <div className="flex items-end justify-between mb-8">
          <div>
            <span className="section-label">Latest</span>
            <h2 className="font-serif text-3xl sm:text-4xl font-semibold mt-2">Fresh off the desk</h2>
          </div>
          <Link to="/archive" className="hidden sm:inline-flex items-center gap-1 text-sm text-accent hover:gap-2 transition-all" data-testid="home-view-archive-link">
            View archive <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        {posts === null ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-6">
            {latest.map((p) => (
              <Link key={p.id} to={`/post/${p.slug}`} className="group flex gap-5 items-start py-4 border-b border-border" data-testid="latest-post-item">
                <div className="card-img-zoom overflow-hidden rounded-lg w-28 h-20 sm:w-36 sm:h-24 shrink-0">
                  <img src={p.cover_image} alt={p.title} loading="lazy" className="w-full h-full object-cover" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                    <span>{p.category_label}</span>
                    {p.tier === "premium" && <Lock className="h-3 w-3 text-accent" />}
                  </div>
                  <h3 className="font-serif text-lg sm:text-xl font-semibold leading-snug mt-1 group-hover:text-accent transition-colors line-clamp-2">
                    {p.title}
                  </h3>
                  <div className="text-xs text-muted-foreground font-mono mt-1.5">
                    {formatDate(p.published_at)} · {p.read_time} min read
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* CONTINUE READING */}
      <ContinueReading />

      {/* FOR YOU */}
      {recs?.posts?.length > 0 && (
        <section className="container-editorial py-6 sm:py-10" data-testid="for-you-section">
          <span className="section-label">For you</span>
          <h2 className="font-serif text-3xl sm:text-4xl font-semibold mt-2 mb-2">Picked for your interests</h2>
          <p className="text-sm text-muted-foreground mb-8" data-testid="for-you-based-on">
            Because you've been reading {recs.based_on.join(" & ")}.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" data-testid="for-you-grid">
            {recs.posts.map((p) => <PostCard key={p.id} post={p} />)}
          </div>
        </section>
      )}

      {/* FILTERABLE GRID */}
      <section className="container-editorial py-6 sm:py-10" data-testid="home-filter-section">
        <span className="section-label">Browse by pillar</span>
        <div className="flex items-center justify-between flex-wrap gap-4 mt-2 mb-8">
          <h2 className="font-serif text-3xl sm:text-4xl font-semibold">Explore the narratives</h2>
        </div>
        <Tabs value={filter} onValueChange={setFilter}>
          <TabsList className="flex flex-wrap h-auto gap-1 bg-muted/60 p-1 mb-8 justify-start">
            <TabsTrigger value="all" data-testid="filter-tab-all">All</TabsTrigger>
            {CATEGORIES.map((c) => (
              <TabsTrigger key={c.slug} value={c.slug} data-testid={`filter-tab-${c.slug}`}>
                {c.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        {posts === null ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">{[...Array(6)].map((_, i) => <Skeleton key={i} className="h-80 rounded-xl" />)}</div>
        ) : (
          <motion.div layout className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" data-testid="home-posts-grid">
            {filtered.map((p, i) => (
              <motion.div key={p.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04, duration: 0.28 }}>
                <PostCard post={p} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </section>

      {/* NEWSLETTER BLOCK */}
      <section className="bg-muted/40 border-y border-border mt-16">
        <div className="container-editorial py-14 sm:py-20">
          <div className="max-w-2xl mx-auto text-center bg-card border border-border rounded-2xl p-8 sm:p-12 shadow-[var(--shadow-soft)]" data-testid="home-newsletter-block">
            <span className="section-label justify-center">The newsletter</span>
            <h2 className="font-serif text-3xl sm:text-4xl font-semibold mt-3">
              One sharp essay. Every week. Zero noise.
            </h2>
            <p className="text-muted-foreground mt-3 mb-7">
              Join readers who get the narrative behind markets, tech, and better living,               before everyone else is talking about it.
            </p>
            <div className="max-w-md mx-auto">
              <NewsletterForm source="home-block" testId="home-block-newsletter-form" />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
