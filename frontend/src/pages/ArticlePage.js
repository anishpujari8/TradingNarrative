import { useEffect, useState, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { Lock, Clock, Check, Sparkles, Highlighter, Share2, Layers, ArrowRight, Flame, Trophy, CalendarClock } from "lucide-react";
import { Seo, metaDescription } from "@/components/Seo";
import { Helmet } from "react-helmet-async";
import { ShareBar } from "@/components/ShareBar";
import { PostCard } from "@/components/PostCard";
import { NewsletterForm } from "@/components/NewsletterForm";
import { CommentsSection } from "@/components/CommentsSection";
import { ReadingProgress } from "@/components/ReadingProgress";
import { BookmarkButton } from "@/components/BookmarkButton";
import { QuoteCardDialog } from "@/components/QuoteCardDialog";
import { AudioNarrator } from "@/components/AudioNarrator";
import { AskEssayWidget } from "@/components/AskEssayWidget";
import { toast } from "sonner";
import { api, formatDate, trackEvent, CATEGORIES, SITE_URL } from "@/lib/api";
import { pillarAccent, withAlpha } from "@/lib/pillars";
import { useAuth } from "@/context/AuthContext";

const Paywall = ({ post }) => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // METER exhausted: anonymous reader has used their 3 free essays
  if (post.lock_reason === "meter") {
    return (
      <div className="my-4" data-testid="meter-paywall-container">
        <Card className="border-accent/40 shadow-[var(--shadow-float)] rounded-2xl">
          <CardContent className="p-8 sm:p-10 text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center mb-4">
              <Lock className="h-5 w-5 text-accent" />
            </div>
            <h3 className="font-serif text-2xl sm:text-3xl font-semibold" data-testid="meter-paywall-title">
              You've read your 3 free essays
            </h3>
            <p className="text-muted-foreground mt-2 max-w-md mx-auto">
              Sharp narratives on markets and the systems behind the desk, every week.
            </p>
            <ul className="text-sm text-left max-w-xs mx-auto mt-5 space-y-2">
              {["The complete essay archive, every pillar", "The 3 latest editions as they publish", "Lounge deep dives, market takes and early drafts"].map((f) => (
                <li key={f} className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-accent mt-0.5 shrink-0" /> {f}
                </li>
              ))}
            </ul>
            <div className="mt-7 flex flex-col gap-3 items-center">
              <Button
                className="bg-accent text-accent-foreground hover:bg-accent/90 h-11 px-8"
                onClick={() => {
                  trackEvent("subscribe_cta_click", `/post/${post.slug}`);
                  navigate("/pricing");
                }}
                data-testid="meter-paywall-subscribe-button"
              >
                <Sparkles className="h-4 w-4 mr-2" /> Go Premium, from ₹99/month
              </Button>
              <button
                className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground transition-colors"
                onClick={() => navigate(`/auth?next=/post/${post.slug}`)}
                data-testid="meter-paywall-signin-link"
              >
                Already a member? Sign in
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="my-4" data-testid="paywall-container">
      <Card className="border-accent/40 shadow-[var(--shadow-float)] rounded-2xl">
        <CardContent className="p-8 sm:p-10 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center mb-4">
            <Lock className="h-5 w-5 text-accent" />
          </div>
          <h3 className="font-serif text-2xl sm:text-3xl font-semibold">
            This story continues for Premium members
          </h3>
          <p className="text-muted-foreground mt-2 max-w-md mx-auto">
            You've read the free preview, {post.total_blocks - post.shown_blocks} more
            paragraphs await. Unlock every essay, ad-free reading, and early access.
          </p>
          <ul className="text-sm text-left max-w-xs mx-auto mt-5 space-y-2">
            {["Full access to all premium essays", "The Lounge: market takes + early drafts", "Full audio narrations", "Cancel anytime"].map((f) => (
              <li key={f} className="flex items-start gap-2">
                <Check className="h-4 w-4 text-accent mt-0.5 shrink-0" /> {f}
              </li>
            ))}
          </ul>
          <div className="mt-7 flex flex-col sm:flex-row gap-3 justify-center">
            <Button
              className="bg-accent text-accent-foreground hover:bg-accent/90 h-11 px-8"
              onClick={() => {
                trackEvent("subscribe_cta_click", `/post/${post.slug}`);
                navigate("/pricing");
              }}
              data-testid="paywall-upgrade-button"
            >
              <Sparkles className="h-4 w-4 mr-2" /> Go Premium
            </Button>
            {!user && (
              <Button variant="outline" className="h-11" onClick={() => navigate(`/auth?next=/post/${post.slug}`)} data-testid="paywall-signin-button">
                Already a member? Sign in
              </Button>
            )}
          </div>
          <p className="text-xs text-muted-foreground font-mono mt-4">From ₹99/month, cancel anytime.</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default function ArticlePage() {
  const { slug } = useParams();
  const { user, loading: authLoading, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [post, setPost] = useState(null);
  const [error, setError] = useState(null);
  const [highlights, setHighlights] = useState([]);
  const [popular, setPopular] = useState([]);
  const [selInfo, setSelInfo] = useState(null);
  const [shareSel, setShareSel] = useState(null);
  const bodyRef = useRef(null);

  // most-highlighted lines across all readers (public, Kindle-style)
  useEffect(() => {
    setPopular([]);
    api.get(`/posts/${encodeURIComponent(slug)}/popular-highlights`)
      .then((res) => setPopular(res.data.popular || []))
      .catch(() => {});
  }, [slug]);

  // load the reader's saved highlights for this essay
  useEffect(() => {
    setHighlights([]);
    if (!user) return;
    api.get(`/highlights?slug=${encodeURIComponent(slug)}`)
      .then((res) => setHighlights(res.data.highlights || []))
      .catch(() => {});
  }, [slug, user?.id]);

  // hide the floating highlight button on scroll
  useEffect(() => {
    if (!selInfo) return;
    const hide = () => setSelInfo(null);
    window.addEventListener("scroll", hide, { passive: true, once: true });
    return () => window.removeEventListener("scroll", hide);
  }, [selInfo]);

  const handleSelection = () => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) { setSelInfo(null); return; }
    const text = sel.toString().trim();
    if (text.length < 3 || text.length > 500) { setSelInfo(null); return; }
    let node = sel.anchorNode;
    while (node && node.nodeType !== 1) node = node.parentNode;
    const blockEl = node?.closest?.("[data-block-index]");
    if (!blockEl) { setSelInfo(null); return; }
    const rect = sel.getRangeAt(0).getBoundingClientRect();
    setSelInfo({
      text,
      blockIndex: parseInt(blockEl.dataset.blockIndex, 10),
      top: Math.max(8, rect.top - 46),
      left: rect.left + rect.width / 2,
    });
  };

  const saveHighlight = () => {
    if (!selInfo) return;
    const { text, blockIndex } = selInfo;
    setSelInfo(null);
    try { window.getSelection()?.removeAllRanges(); } catch (e) { console.debug("selection clear failed", e); }
    if (!user) {
      toast("Sign in to save highlights", {
        description: "Create a free account to keep your favourite lines.",
        action: { label: "Sign in", onClick: () => navigate(`/auth?next=/post/${slug}`) },
      });
      return;
    }
    api.post("/highlights", { slug, block_index: blockIndex, text })
      .then((res) => {
        if (!res.data.already) setHighlights((h) => [res.data, ...h]);
        toast.success(res.data.already ? "Already in your highlights" : "Saved to your highlights", {
          action: { label: "View", onClick: () => navigate("/highlights") },
        });
      })
      .catch((err) => toast.error(err?.response?.data?.detail || "Could not save the highlight."));
  };

  const shareSelection = () => {
    if (!selInfo || !post) return;
    const { text } = selInfo;
    setSelInfo(null);
    try { window.getSelection()?.removeAllRanges(); } catch (e) { console.debug("selection clear failed", e); }
    setShareSel({ text, post_title: post.title, category_label: post.category_label, category: post.category });
  };

  const renderWithHighlights = (text, blockIndex) => {
    const personal = highlights.filter((h) => h.block_index === blockIndex).map((h) => h.text);
    const pops = popular.filter((p) => p.block_index === blockIndex);
    if (!personal.length && !pops.length) return text;
    let parts = [text];
    const splitWrap = (m, make) => {
      parts = parts.flatMap((seg) => {
        if (typeof seg !== "string") return [seg];
        const idx = seg.indexOf(m);
        if (idx === -1) return [seg];
        return [seg.slice(0, idx), make(), seg.slice(idx + m.length)];
      });
    };
    // personal marks take precedence; popular applies to remaining plain segments
    personal.forEach((m) => splitWrap(m, () => ({ mark: m, type: "personal" })));
    pops.forEach((p) => splitWrap(p.text, () => ({ mark: p.text, type: "popular", count: p.count })));
    return parts.map((seg, j) => {
      if (typeof seg === "string") return seg;
      if (seg.type === "personal") return <mark key={j} className="reader-highlight">{seg.mark}</mark>;
      return (
        <mark key={j} className="popular-highlight" title={`${seg.count} readers highlighted this`} data-testid="popular-highlight">
          {seg.mark}
          <span className="popular-count" aria-label={`${seg.count} readers highlighted this`}>{seg.count}</span>
        </mark>
      );
    });
  };

  useEffect(() => {
    if (authLoading) return;
    setPost(null);
    setError(null);
    api
      .get(`/posts/${slug}`)
      .then((res) => {
        setPost(res.data);
        try {
          const hist = JSON.parse(localStorage.getItem("ttn_read_history") || "[]").filter((h) => h.slug !== res.data.slug);
          hist.unshift({ slug: res.data.slug, category: res.data.category });
          localStorage.setItem("ttn_read_history", JSON.stringify(hist.slice(0, 50)));
        } catch (e) { console.debug("read history save failed", e); }
        try {
          const map = JSON.parse(localStorage.getItem("ttn_progress") || "{}");
          const saved = map[res.data.slug];
          if (saved && saved.p > 0.05 && saved.p < 0.95) {
            setTimeout(() => {
              toast("Pick up where you left off?", {
                description: `You were ${Math.round(saved.p * 100)}% through this essay.`,
                action: {
                  label: "Resume",
                  onClick: () => {
                    const el = bodyRef.current;
                    if (!el) return;
                    const rect = el.getBoundingClientRect();
                    const elTop = rect.top + window.scrollY;
                    const total = rect.height - window.innerHeight * 0.5;
                    window.scrollTo({ top: elTop - window.innerHeight * 0.25 + saved.p * total, behavior: "smooth" });
                  },
                },
                duration: 6000,
              });
            }, 700);
          }
        } catch (e) { console.debug("resume progress restore failed", e); }
      })
      .catch((err) => setError(err?.response?.status === 404 ? "This post doesn't exist." : "Failed to load the article."));
  }, [slug, authLoading, user?.is_premium]);

  // reading streak: count this essay toward the reader's daily streak (once per essay visit)
  const streakSent = useRef(false);
  useEffect(() => { streakSent.current = false; }, [slug]);
  useEffect(() => {
    if (!post || !user || streakSent.current) return;
    streakSent.current = true;
    api.post("/users/streak/read", { tz_offset_minutes: new Date().getTimezoneOffset(), slug })
      .then((res) => {
        if (!res.data?.extended) return;
        refreshUser();
        const s = res.data.current_streak;
        if (res.data.milestone) {
          // milestone celebration: 7 / 30 / 100 consecutive days — badge earned
          toast.success(`${res.data.milestone}-day streak, badge earned!`, {
            description: `Incredible consistency. The ${res.data.milestone}-Day Reader badge is now on your account page.`,
            icon: <Trophy className="h-4 w-4 text-accent" />,
            duration: 7000,
            action: { label: "See badge", onClick: () => navigate("/account") },
          });
          return;
        }
        toast(s > 1 ? `${s}-day reading streak` : "Reading streak started", {
          description: s > 1 ? "You've read on consecutive days. Keep it going tomorrow." : "Come back tomorrow to build your streak.",
          icon: <Flame className="h-4 w-4 text-accent" />,
          duration: 4000,
        });
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [post, user?.id]);

  if (error) {
    return (
      <div className="container-editorial py-24 text-center" data-testid="article-error">
        <h1 className="font-serif text-3xl font-semibold mb-3">{error}</h1>
        <Link to="/" className="editorial-link text-accent">Back to the homepage</Link>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="container-editorial py-16 reading-col space-y-6">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="aspect-[16/9] w-full rounded-2xl" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const visibleBlocks = post.is_locked ? post.content_blocks.slice(0, -1) : post.content_blocks;
  const blurredBlock = post.is_locked ? post.content_blocks[post.content_blocks.length - 1] : null;

  // Paywall structured data (schema.org NewsArticle) — Google-compliant paywall signalling,
  // plus BreadcrumbList so search engines and AI assistants understand site hierarchy
  const categoryLabel = CATEGORIES.find((c) => c.slug === post.category)?.label || post.category;
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "NewsArticle",
        headline: post.title,
        datePublished: post.published_at,
        dateModified: post.updated_at || post.published_at,
        author: { "@type": "Person", name: post.author || "Anish Pujari" },
        publisher: {
          "@type": "Organization",
          name: "The Trading Narrative",
          logo: { "@type": "ImageObject", url: `${window.location.origin}/logo.png` },
        },
        description: metaDescription(post),
        keywords: (post.tags || []).join(", "),
        mainEntityOfPage: `${window.location.origin}/post/${post.slug}`,
        image: post.cover_image,
        isAccessibleForFree: post.tier !== "premium",
        ...(post.tier === "premium"
          ? { hasPart: { "@type": "WebPageElement", isAccessibleForFree: false, cssSelector: ".paywalled-content" } }
          : {}),
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "Home", item: window.location.origin },
          { "@type": "ListItem", position: 2, name: categoryLabel, item: `${window.location.origin}/topics/${post.category}` },
          { "@type": "ListItem", position: 3, name: post.title, item: `${window.location.origin}/post/${post.slug}` },
        ],
      },
    ],
  };

  return (
    <article data-testid="article-page">
      <Seo
        title={post.title}
        description={metaDescription(post)}
        keywords={post.tags?.length ? `${post.tags.join(", ")}, commodity trading, trading technology` : undefined}
        image={`${SITE_URL}/api/og/${post.slug}.png`}
        path={`/post/${post.slug}`}
        type="article"
      />
      <Helmet>
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      </Helmet>
      <ReadingProgress targetRef={bodyRef} readTime={post.read_time} slug={post.slug} accent={pillarAccent(post.category)} />

      {selInfo && (
        <div
          className="fixed z-[200] -translate-x-1/2 flex items-center rounded-full bg-foreground text-background shadow-lg overflow-hidden"
          style={{ top: selInfo.top, left: selInfo.left }}
          onMouseDown={(e) => e.preventDefault()}
          data-testid="selection-popover"
        >
          <button
            className="inline-flex items-center gap-1.5 text-xs font-medium pl-3.5 pr-3 py-2 hover:bg-accent hover:text-accent-foreground transition-colors duration-150"
            onClick={saveHighlight}
            data-testid="highlight-save-button"
            aria-label="Save highlight"
          >
            <Highlighter className="h-3.5 w-3.5" /> Highlight
          </button>
          <span className="w-px self-stretch my-1.5 bg-background/25" aria-hidden="true" />
          <button
            className="inline-flex items-center gap-1.5 text-xs font-medium pl-3 pr-3.5 py-2 hover:bg-accent hover:text-accent-foreground transition-colors duration-150"
            onClick={shareSelection}
            data-testid="selection-share-button"
            aria-label="Share as quote card"
          >
            <Share2 className="h-3.5 w-3.5" /> Share
          </button>
        </div>
      )}

      <div className="container-editorial pt-10 sm:pt-14">
        <div className="reading-col">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <div className="flex items-center gap-2 flex-wrap">
              <Link to={`/topics/${post.category}`}>
                <Badge
                  className="font-mono text-[10px] uppercase tracking-wider border transition-opacity hover:opacity-80"
                  style={{
                    backgroundColor: withAlpha(pillarAccent(post.category), 0.12),
                    color: pillarAccent(post.category),
                    borderColor: withAlpha(pillarAccent(post.category), 0.3),
                  }}
                  data-testid="article-category-badge"
                >
                  {post.category_label}
                </Badge>
              </Link>
              {post.edition && (
                <Link to="/briefings" data-testid="article-edition-badge">
                  <Badge className="bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 font-mono text-[10px] cursor-pointer">
                    Edition #{post.edition}
                  </Badge>
                </Link>
              )}
              {post.tier === "premium" && (
                <Badge className="bg-accent/10 text-accent border border-accent/30 hover:bg-accent/10 gap-1" data-testid="article-premium-badge">
                  <Lock className="h-3 w-3" /> Premium
                </Badge>
              )}
            </div>
            <h1 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-semibold leading-[1.1] mt-4" data-testid="article-title">
              {post.title}
            </h1>
            <p className="text-muted-foreground text-lg mt-4">{post.excerpt}</p>
            {post.tags?.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-4" data-testid="article-tags">
                {post.tags.map((t) => (
                  <Link key={t} to={`/archive?tag=${encodeURIComponent(t)}`} className="text-xs font-mono px-2.5 py-1 rounded-full border border-border text-muted-foreground hover:border-accent hover:text-accent transition-colors" data-testid="article-tag-chip">
                    #{t}
                  </Link>
                ))}
              </div>
            )}
            <div className="flex items-center justify-between gap-3 mt-6 flex-wrap">
              <div className="flex items-center gap-3">
              <Avatar className="h-10 w-10 border border-border">
                <AvatarImage src={post.author?.avatar} alt={post.author?.name} />
                <AvatarFallback>{post.author?.name?.slice(0, 2)}</AvatarFallback>
              </Avatar>
              <div className="text-sm">
                <div className="font-medium" data-testid="article-author-name">{post.author?.name}</div>
                <div className="text-muted-foreground text-xs font-mono flex items-center gap-2">
                  <span>{formatDate(post.published_at)}</span>·
                  <span className="inline-flex items-center gap-1" data-testid="article-read-time"><Clock className="h-3 w-3" /> {post.read_time} min read</span>
                </div>
              </div>
              </div>
              <BookmarkButton postId={post.id} />
            </div>
          </motion.div>

          <div className="card-img-zoom overflow-hidden rounded-2xl border border-border mt-8 lg:-mx-16">
            <img src={post.cover_image} alt={post.title} className="w-full aspect-[16/9] object-cover" data-testid="article-cover-image" />
          </div>

          {/* Mobile share bar */}
          <div className="lg:hidden mt-6">
            <ShareBar post={post} idSuffix="-mobile" />
          </div>
        </div>

        <div className="relative reading-col mt-10" ref={bodyRef}>
          {/* Desktop share rail */}
          <div className="hidden lg:block absolute -left-24 top-0 h-full">
            <div className="sticky top-28">
              <ShareBar post={post} orientation="vertical" />
            </div>
          </div>

          {post.series && (
            <Link
              to={`/series/${post.series.slug}`}
              className="group flex items-center gap-2 rounded-xl border border-accent/30 bg-accent/5 px-4 py-3 mb-5 text-sm hover:border-accent/60 transition-colors"
              data-testid="article-series-banner"
            >
              <Layers className="h-4 w-4 text-accent shrink-0" />
              <span>Part of the <strong className="font-semibold">{post.series.title}</strong> series</span>
              <span className="ml-auto inline-flex items-center gap-1 text-accent font-medium">
                View all <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
              </span>
            </Link>
          )}

          {/* METER banner: persistent, never blocks reading */}
          {post.meter && post.meter.granted && (
            <div className="mb-6 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border bg-secondary/40 px-4 py-2.5 text-sm" data-testid="meter-banner">
              <span className="text-muted-foreground" data-testid="meter-banner-count">
                <strong className="text-foreground font-medium">{post.meter.remaining} of {post.meter.limit}</strong> free essays remaining
              </span>
              <Link to="/pricing" className="text-accent font-medium hover:underline underline-offset-4" data-testid="meter-banner-subscribe-link">
                Subscribe for unlimited access
              </Link>
            </div>
          )}

          {post.early_access && (
            <div className="mb-6 flex items-center gap-2.5 rounded-xl border border-accent/40 bg-accent/5 px-4 py-3 text-sm" data-testid="early-access-notice">
              <CalendarClock className="h-4 w-4 text-accent shrink-0" />
              <span>
                <strong className="font-medium">Early access</strong>, a Lounge exclusive. This publishes for everyone on{" "}
                {formatDate(post.publish_at)}.
              </span>
            </div>
          )}

          <AudioNarrator slug={slug} />

          <div className="article-body" data-testid="article-body" onMouseUp={handleSelection} onTouchEnd={handleSelection}>
            {visibleBlocks.map((block, i) =>
              block.startsWith("## ") ? (
                <h2 key={i} className="font-serif text-2xl font-semibold mt-10 mb-4" data-block-index={i}>{block.slice(3)}</h2>
              ) : (
                <p key={i} data-block-index={i}>{renderWithHighlights(block, i)}</p>
              )
            )}
            {post.is_locked && blurredBlock && (
              <div className="paywalled-content">
                <div className="paywall-fade" data-testid="paywall-blurred-content">
                  <p className="paywall-blur" aria-hidden="true">{blurredBlock}</p>
                </div>
              </div>
            )}
          </div>

          {post.is_locked && <Paywall post={post} />}

          <AskEssayWidget slug={slug} />

          {!post.is_locked && (
            <div className="mt-12 bg-muted/40 border border-border rounded-2xl p-6 sm:p-8" data-testid="article-inline-newsletter">
              <span className="section-label">Enjoyed this?</span>
              <h3 className="font-serif text-2xl font-semibold mt-2 mb-1">Get the next one in your inbox</h3>
              <p className="text-sm text-muted-foreground mb-4">One sharp essay a week. Unsubscribe anytime.</p>
              <NewsletterForm source={`article:${post.slug}`} testId="article-newsletter-form" />
            </div>
          )}

          <Separator className="my-10" />

          {/* Author bio */}
          <div className="flex gap-4 items-start" data-testid="article-author-bio">
            <Avatar className="h-14 w-14 border border-border">
              <AvatarImage src={post.author?.avatar} alt={post.author?.name} />
              <AvatarFallback>{post.author?.name?.slice(0, 2)}</AvatarFallback>
            </Avatar>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Written by</div>
              <div className="font-serif text-xl font-semibold">{post.author?.name}</div>
              <p className="text-sm text-muted-foreground mt-1">{post.author?.bio}</p>
              <Link to="/about" className="editorial-link text-accent text-sm mt-2 inline-block">More about the author</Link>
            </div>
          </div>

          <Separator className="my-10" />

          {/* Member discussion */}
          <CommentsSection post={post} />
        </div>

        {/* Related */}
        {post.related?.length > 0 && (
          <section className="mt-16 pb-4" data-testid="article-related-section">
            <span className="section-label">Keep reading</span>
            <h2 className="font-serif text-3xl font-semibold mt-2 mb-8">Related narratives</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {post.related.map((r) => (
                <PostCard key={r.id} post={r} />
              ))}
            </div>
          </section>
        )}
      </div>

      <QuoteCardDialog highlight={shareSel} open={!!shareSel} onOpenChange={(o) => !o && setShareSel(null)} />
    </article>
  );
}
