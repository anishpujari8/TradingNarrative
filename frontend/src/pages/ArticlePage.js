import { useEffect, useState, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { Lock, Clock, Check, Sparkles } from "lucide-react";
import { Seo } from "@/components/Seo";
import { ShareBar } from "@/components/ShareBar";
import { PostCard } from "@/components/PostCard";
import { NewsletterForm } from "@/components/NewsletterForm";
import { CommentsSection } from "@/components/CommentsSection";
import { ReadingProgress } from "@/components/ReadingProgress";
import { BookmarkButton } from "@/components/BookmarkButton";
import { toast } from "sonner";
import { api, formatDate, trackEvent } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const Paywall = ({ post }) => {
  const navigate = useNavigate();
  const { user } = useAuth();
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
            You've read the free preview — {post.total_blocks - post.shown_blocks} more
            paragraphs await. Unlock every essay, ad-free reading, and early access.
          </p>
          <ul className="text-sm text-left max-w-xs mx-auto mt-5 space-y-2">
            {["Full access to all premium essays", "Ad-free, distraction-free reading", "Early access to new posts", "Cancel anytime"].map((f) => (
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
          <p className="text-xs text-muted-foreground font-mono mt-4">From $6.67/month, billed annually.</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default function ArticlePage() {
  const { slug } = useParams();
  const { user, loading: authLoading } = useAuth();
  const [post, setPost] = useState(null);
  const [error, setError] = useState(null);
  const bodyRef = useRef(null);

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
        } catch { /* ignore */ }
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
        } catch { /* ignore */ }
      })
      .catch((err) => setError(err?.response?.status === 404 ? "This post doesn't exist." : "Failed to load the article."));
  }, [slug, authLoading, user?.is_premium]);

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

  return (
    <article data-testid="article-page">
      <Seo title={post.title} description={post.excerpt} image={post.cover_image} path={`/post/${post.slug}`} type="article" />
      <ReadingProgress targetRef={bodyRef} readTime={post.read_time} slug={post.slug} />

      <div className="container-editorial pt-10 sm:pt-14">
        <div className="reading-col">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <div className="flex items-center gap-2 flex-wrap">
              <Link to={`/category/${post.category}`}>
                <Badge variant="secondary" className="font-mono text-[10px] uppercase tracking-wider hover:bg-accent/10 hover:text-accent transition-colors" data-testid="article-category-badge">
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

          <div className="article-body" data-testid="article-body">
            {visibleBlocks.map((block, i) =>
              block.startsWith("## ") ? (
                <h2 key={i} className="font-serif text-2xl font-semibold mt-10 mb-4">{block.slice(3)}</h2>
              ) : (
                <p key={i}>{block}</p>
              )
            )}
            {post.is_locked && blurredBlock && (
              <div className="paywall-fade" data-testid="paywall-blurred-content">
                <p className="paywall-blur" aria-hidden="true">{blurredBlock}</p>
              </div>
            )}
          </div>

          {post.is_locked && <Paywall post={post} />}

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
    </article>
  );
}
