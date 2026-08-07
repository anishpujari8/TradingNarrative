import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Highlighter, Trash2, ArrowUpRight } from "lucide-react";
import { toast } from "sonner";
import { Seo } from "@/components/Seo";
import { api, formatDate } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function HighlightsPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [highlights, setHighlights] = useState(null);

  useEffect(() => {
    if (!loading && !user) {
      navigate("/auth?next=/highlights");
      return;
    }
    if (user) {
      api.get("/highlights").then((res) => setHighlights(res.data.highlights)).catch(() => setHighlights([]));
    }
  }, [user, loading, navigate]);

  const remove = (hid) => {
    const prev = highlights;
    setHighlights((h) => h.filter((x) => x.id !== hid));
    api.delete(`/highlights/${hid}`).then(() => {
      toast.success("Highlight removed");
    }).catch(() => {
      setHighlights(prev);
      toast.error("Could not remove the highlight. Try again.");
    });
  };

  if (loading || !user) {
    return <div className="container-editorial py-16"><Skeleton className="h-64 rounded-2xl" /></div>;
  }

  // group by essay, preserving newest-first order
  const groups = [];
  if (highlights) {
    const bySlug = {};
    for (const h of highlights) {
      if (!bySlug[h.post_slug]) {
        bySlug[h.post_slug] = { slug: h.post_slug, title: h.post_title, category_label: h.category_label, items: [] };
        groups.push(bySlug[h.post_slug]);
      }
      bySlug[h.post_slug].items.push(h);
    }
  }

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="highlights-page">
      <Seo title="Your Highlights" description="Lines you've saved from essays." path="/highlights" />
      <span className="section-label">Saved lines</span>
      <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3">Your highlights</h1>
      <p className="text-muted-foreground text-lg mt-3">Every line you've highlighted, kept in one place.</p>
      <Separator className="my-10" />

      {highlights === null ? (
        <div className="space-y-4">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)}</div>
      ) : highlights.length === 0 ? (
        <div className="text-center py-16" data-testid="highlights-empty">
          <Highlighter className="h-10 w-10 text-muted-foreground/50 mx-auto mb-4" />
          <h2 className="font-serif text-2xl font-semibold">No highlights yet</h2>
          <p className="text-muted-foreground mt-2 mb-6 max-w-md mx-auto">
            Select any line while reading an essay and tap "Highlight" to save it here.
          </p>
          <Link to="/archive"><Button className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="highlights-browse-button">Browse the essays</Button></Link>
        </div>
      ) : (
        <div className="space-y-12" data-testid="highlights-list">
          {groups.map((g) => (
            <section key={g.slug} data-testid={`highlights-group-${g.slug}`}>
              <div className="flex items-center gap-3 flex-wrap mb-4">
                <Badge variant="secondary" className="font-mono text-[10px] uppercase tracking-wider">{g.category_label}</Badge>
                <Link to={`/post/${g.slug}`} className="group inline-flex items-center gap-1 font-serif text-xl font-semibold hover:text-accent transition-colors" data-testid={`highlights-post-link-${g.slug}`}>
                  {g.title}
                  <ArrowUpRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              </div>
              <div className="space-y-3">
                {g.items.map((h) => (
                  <div key={h.id} className="group flex items-start gap-3 rounded-xl border border-border bg-card p-5 hover:border-accent/40 transition-colors" data-testid={`highlight-card-${h.id}`}>
                    <div className="w-1 self-stretch rounded-full bg-accent/60 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <blockquote className="font-serif text-lg leading-relaxed" data-testid="highlight-text">
                        &ldquo;{h.text}&rdquo;
                      </blockquote>
                      <div className="text-xs text-muted-foreground font-mono mt-2">Saved {formatDate(h.created_at)}</div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-destructive shrink-0"
                      onClick={() => remove(h.id)}
                      aria-label="Remove highlight"
                      data-testid={`highlight-delete-${h.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
