import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Highlighter, Trash2, ArrowUpRight, StickyNote, Pencil, Share2 } from "lucide-react";
import { toast } from "sonner";
import { Seo } from "@/components/Seo";
import { QuoteCardDialog } from "@/components/QuoteCardDialog";
import { api, formatDate } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function HighlightsPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [highlights, setHighlights] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [noteDraft, setNoteDraft] = useState("");
  const [savingNote, setSavingNote] = useState(false);
  const [shareTarget, setShareTarget] = useState(null);

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

  const startNote = (h) => {
    setEditingId(h.id);
    setNoteDraft(h.note || "");
  };

  const saveNote = (hid) => {
    setSavingNote(true);
    api.put(`/highlights/${hid}/note`, { note: noteDraft })
      .then((res) => {
        setHighlights((hs) => hs.map((x) => (x.id === hid ? { ...x, note: res.data.note } : x)));
        setEditingId(null);
        toast.success(noteDraft.trim() ? "Note saved" : "Note removed");
      })
      .catch(() => toast.error("Could not save the note. Try again."))
      .finally(() => setSavingNote(false));
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

                      {editingId === h.id ? (
                        <div className="mt-3 space-y-2" data-testid="highlight-note-editor">
                          <Textarea
                            value={noteDraft}
                            onChange={(e) => setNoteDraft(e.target.value)}
                            maxLength={500}
                            rows={2}
                            placeholder="Why did this line stick with you?"
                            className="text-sm"
                            data-testid="highlight-note-input"
                            autoFocus
                          />
                          <div className="flex items-center gap-2">
                            <Button size="sm" className="bg-accent text-accent-foreground hover:bg-accent/90 h-8" onClick={() => saveNote(h.id)} disabled={savingNote} data-testid="highlight-note-save">
                              Save note
                            </Button>
                            <Button size="sm" variant="ghost" className="h-8" onClick={() => setEditingId(null)} data-testid="highlight-note-cancel">
                              Cancel
                            </Button>
                            <span className="text-[11px] text-muted-foreground font-mono ml-auto">{noteDraft.length}/500</span>
                          </div>
                        </div>
                      ) : h.note ? (
                        <div className="mt-3 flex items-start gap-2 rounded-lg bg-muted/50 border border-border/60 px-3 py-2" data-testid="highlight-note">
                          <StickyNote className="h-3.5 w-3.5 text-accent mt-0.5 shrink-0" />
                          <p className="text-sm text-foreground/80 flex-1">{h.note}</p>
                          <button className="text-muted-foreground hover:text-accent transition-colors" onClick={() => startNote(h)} aria-label="Edit note" data-testid="highlight-note-edit">
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      ) : null}

                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-xs text-muted-foreground font-mono">Saved {formatDate(h.created_at)}</span>
                        {!h.note && editingId !== h.id && (
                          <button className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-accent transition-colors" onClick={() => startNote(h)} data-testid="highlight-add-note">
                            <StickyNote className="h-3 w-3" /> Add note
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col gap-1 shrink-0">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-muted-foreground hover:text-accent"
                        onClick={() => setShareTarget(h)}
                        aria-label="Share as quote card"
                        data-testid={`highlight-share-${h.id}`}
                      >
                        <Share2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-muted-foreground hover:text-destructive"
                        onClick={() => remove(h.id)}
                        aria-label="Remove highlight"
                        data-testid={`highlight-delete-${h.id}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      <QuoteCardDialog highlight={shareTarget} open={!!shareTarget} onOpenChange={(o) => !o && setShareTarget(null)} />
    </div>
  );
}
