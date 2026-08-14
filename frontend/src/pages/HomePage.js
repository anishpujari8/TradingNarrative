import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Lock, Clock, ArrowRight, Zap, Crown } from "lucide-react";
import { Seo } from "@/components/Seo";
import { PostCard } from "@/components/PostCard";
import { NewsletterForm } from "@/components/NewsletterForm";
import { api, CATEGORIES, formatDate, SITE_URL, SITE_NAME, getPreferredCurrency, formatINR } from "@/lib/api";
import { pillarAccent, withAlpha, PillarMotif, PILLAR_TAGLINES, pillarMascot, PILLAR_MASCOT_ALTS } from "@/lib/pillars";
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
  const [earlyBird, setEarlyBird] = useState(null); // premium early bird promo (first 50)

  useEffect(() => {
    api.get("/early-supporters").then((res) => setPromo(res.data)).catch(() => {});
    api.get("/billing/early-bird").then((res) => setEarlyBird(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (authLoading) return;
    let slugs = [];
    try {
      slugs = JSON.parse(localStorage.getItem("ttn_read_history") || "[]").map((h) => h.slug);
    } catch (e) { console.debug("read history parse failed", e); }
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
      <Seo
        path="/"
        jsonLd={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "WebSite",
              "@id": `${SITE_URL}/#website`,
              name: SITE_NAME,
              alternateName: ["Trading Narrative", "The Trading Narrative Newsletter"],
              url: SITE_URL,
              description:
                "Commodity trading and tech insights: energy markets, trading technology, ETRM systems, market risk, freight and shipping markets, plus a weekly briefing newsletter.",
              publisher: { "@id": `${SITE_URL}/#organization` },
              inLanguage: "en",
            },
            {
              "@type": "Organization",
              "@id": `${SITE_URL}/#organization`,
              name: SITE_NAME,
              url: SITE_URL,
              logo: { "@type": "ImageObject", url: `${SITE_URL}/logo.png` },
              founder: { "@type": "Person", name: "Anish Pujari" },
              knowsAbout: [
                "commodity trading", "energy markets", "trading technology", "ETRM", "CTRM",
                "market risk", "freight markets", "shipping industry", "business and finance",
              ],
            },
          ],
        }}
      />

      {/* EARLY BIRD PREMIUM DEAL, first 50 premium subscribers get a discounted first period */}
      {earlyBird?.active && !user?.is_premium && (() => {
        const isINR = getPreferredCurrency() === "inr";
        const m = earlyBird.plans?.monthly;
        const a = earlyBird.plans?.annual;
        if (!m || !a) return null;
        const monthly = isINR ? formatINR(m.amount_inr) : `$${m.amount.toFixed(2)}`;
        const annualP = isINR ? formatINR(a.amount_inr) : `$${a.amount.toFixed(2)}`;
        const annualReg = isINR ? formatINR(a.regular_amount_inr) : `$${a.regular_amount.toFixed(2)}`;
        return (
          <div className="bg-foreground text-background" data-testid="early-bird-banner">
            <Link
              to="/pricing"
              className="container-editorial flex items-center justify-center gap-2 py-2.5 text-sm hover:opacity-90 transition-opacity"
              data-testid="early-bird-banner-link"
            >
              <Crown className="h-3.5 w-3.5 shrink-0 text-accent" />
              <span className="truncate">
                Early bird: go Premium for <strong>{monthly}</strong> first month or{" "}
                <strong>{annualP}</strong> first year <span className="opacity-70 line-through">{annualReg}</span>
                {earlyBird.remaining < earlyBird.spots ? (
                  <>
                    {" "}· <strong data-testid="early-bird-banner-count">{earlyBird.remaining} of {earlyBird.spots}</strong> spots left
                  </>
                ) : (
                  <> · early-bird pricing for the first {earlyBird.spots} members</>
                )}
              </span>
              <span className="hidden sm:inline-flex items-center gap-1 font-medium underline underline-offset-4 shrink-0">
                Lock in the deal <ArrowRight className="h-3.5 w-3.5" />
              </span>
            </Link>
          </div>
        );
      })()}

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
              {promo.taken > 0 ? (
                <>
                  Early supporter offer, <strong data-testid="early-supporter-count">{promo.left} of {promo.limit}</strong> spots
                  left · first 5 essays free for early readers
                </>
              ) : (
                <>
                  Be one of the first <strong data-testid="early-supporter-count">{promo.limit}</strong> early readers · first 5 essays free
                </>
              )}
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
              <p className="text-xs text-muted-foreground mt-2 font-mono" data-testid="hero-social-proof">
                Join 500+ commodity trading professionals · Free forever. Premium if you want everything.
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

      {/* AUTHOR STRIP, credibility above the fold */}
      <section className="container-editorial" data-testid="home-author-strip">
        <div className="flex items-center gap-4 py-5 border-b border-border flex-wrap">
          <img
            src="/anish.jpg"
            alt="Anish Pujari, author of The Trading Narrative"
            className="h-12 w-12 rounded-full object-cover border-2 border-accent/40 shrink-0"
            loading="lazy"
            data-testid="home-author-photo"
          />
          <p className="text-sm text-muted-foreground flex-1 min-w-[240px]">
            <span className="text-foreground font-medium">By Anish Pujari</span> — ETRM product leader
            with 12 years delivering commodity trading systems, author of{" "}
            <em className="text-foreground">How Trading Can Make You Money</em>.
          </p>
          <div className="flex items-center gap-4 shrink-0">
            <Link to="/about" className="text-sm text-accent font-medium hover:underline" data-testid="home-author-about-link">
              About the author
            </Link>
            <a
              href="https://www.linkedin.com/build-relation/newsletter-follow?entityUrn=7490310794455306241"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-accent font-medium hover:underline"
              data-testid="home-author-linkedin-newsletter-link"
            >
              Subscribe on LinkedIn
            </a>
          </div>
        </div>
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
                  <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider">
                    <span style={{ color: pillarAccent(p.category) }}>{p.category_label}</span>
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

      {/* START HERE, FREE, sample the quality before the paywall */}
      {posts?.some((p) => p.tier === "free") && (() => {
        const preferred = [
          "etrm-vs-ctrm-whats-the-difference-and-which-one-do-you-actually-need",
          "the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a",
          "the-boring-portfolio-that-beats-your-broker",
        ];
        const freePosts = posts.filter((p) => p.tier === "free");
        const picks = [
          ...preferred.map((s) => freePosts.find((p) => p.slug === s)).filter(Boolean),
          ...freePosts.filter((p) => !preferred.includes(p.slug)),
        ].slice(0, 3);
        if (!picks.length) return null;
        return (
          <section className="container-editorial py-6 sm:py-10" data-testid="home-free-reads-section">
            <div className="flex items-end justify-between mb-8 flex-wrap gap-3">
              <div>
                <span className="section-label">Start here, free</span>
                <h2 className="font-serif text-3xl sm:text-4xl font-semibold mt-2">
                  Sample the quality, no sign-up needed
                </h2>
                <p className="text-sm text-muted-foreground mt-2 max-w-xl">
                  Three full essays, free for everyone. If they earn your trust, the rest of the
                  library is one step away.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" data-testid="home-free-reads-grid">
              {picks.map((p) => <PostCard key={p.id} post={p} />)}
            </div>
          </section>
        );
      })()}

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
              <TabsTrigger key={c.slug} value={c.slug} data-testid={`filter-tab-${c.slug}`} className="gap-1.5">
                <span
                  className="inline-block h-2 w-2 rounded-full shrink-0"
                  style={{ backgroundColor: pillarAccent(c.slug) }}
                  aria-hidden
                />
                {c.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        {filter !== "all" && (() => {
          const c = CATEGORIES.find((x) => x.slug === filter);
          const accent = pillarAccent(filter);
          return (
            <div
              className="relative overflow-hidden rounded-2xl border px-6 sm:px-8 py-6 mb-8"
              style={{ borderColor: withAlpha(accent, 0.35), backgroundColor: withAlpha(accent, 0.07) }}
              data-testid={`pillar-header-${filter}`}
            >
              <div className="absolute inset-y-0 right-0 w-2/3 sm:w-1/2 pointer-events-none" style={{ color: accent, opacity: 0.18 }}>
                <PillarMotif category={filter} className="h-full w-full" />
              </div>
              <div className="relative flex items-center gap-5 sm:gap-8">
                <div className="min-w-0 flex-1">
                  <span className="font-mono text-[11px] uppercase tracking-[0.18em]" style={{ color: accent }}>
                    Pillar
                  </span>
                  <h3 className="font-serif text-2xl sm:text-3xl font-semibold mt-1">{c?.label}</h3>
                  <p className="text-sm text-muted-foreground mt-1.5 max-w-md">{PILLAR_TAGLINES[filter]}</p>
                  <Link
                    to={`/topics/${filter}`}
                    className="inline-flex items-center gap-1 text-sm font-medium mt-3 hover:gap-2 transition-all"
                    style={{ color: accent }}
                    data-testid={`pillar-header-hub-link-${filter}`}
                  >
                    Visit the {c?.label} hub <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
                <img
                  src={pillarMascot(filter)}
                  alt={PILLAR_MASCOT_ALTS[filter]}
                  className="hidden sm:block h-24 w-24 lg:h-28 lg:w-28 rounded-full object-cover shrink-0 shadow-md"
                  style={{ border: `3px solid ${withAlpha(accent, 0.55)}` }}
                  loading="lazy"
                  data-testid={`pillar-mascot-home-${filter}`}
                />
              </div>
            </div>
          );
        })()}
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
              <p className="text-xs text-muted-foreground mt-3 font-mono" data-testid="home-block-social-proof">
                Join 500+ commodity trading professionals reading every week.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
