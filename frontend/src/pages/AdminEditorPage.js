import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { ArrowLeft, Save, Loader2, LayoutTemplate, Wand2 } from "lucide-react";
import { toast } from "sonner";
import { Seo } from "@/components/Seo";
import { AiAssistantDialog } from "@/components/AiAssistantDialog";
import { api, CATEGORIES } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const emptyForm = {
  title: "",
  excerpt: "",
  category: "tech-business",
  tier: "free",
  cover_image: "",
  content: "",
  tags: "",
  featured: false,
  status: "draft",
  publish_at: "",
  edition: "",
};

const briefingTemplate = (edition) => ({
  title: "Five Things Commodity Desks Need to Know This Week",
  excerpt: `Your Wednesday briefing on trading technology, markets, risk and regulation — in 5 minutes. Edition #${edition} of The Trading Narrative.`,
  category: "finance",
  tier: "free",
  tags: "ETRM, Commodities, Markets, Risk, Regulation",
  edition: String(edition),
  content: [
    "THE BOARD — Brent $__ ▲ | WTI $__ ▲ | Copper $__ ▲ | Wheat $__ | Corn $__ | Soybeans $__",
    `Welcome to Edition #${edition}. Every week: five things that actually change how trading and risk teams work — written the way a desk reads them, not the way a press release writes them.`,
    "## 1. [First headline]",
    "[What happened, and why it changes how the desk works. End with the tell — the detail that proves the point.] (Sources: …)",
    "## 2. [Second headline]",
    "[What happened, and why it matters.] (Sources: …)",
    "## 3. [Third headline]",
    "[What happened, and why it matters.] (Sources: …)",
    "## 4. [Fourth headline]",
    "[What happened, and why it matters.] (Sources: …)",
    "## 5. [Fifth headline]",
    "[What happened, and why it matters.] (Sources: …)",
    "## Three signals to watch",
    "1. [Signal one — what to watch and why.]",
    "2. [Signal two — what to watch and why.]",
    "3. [Signal three — what to watch and why.]",
    "If this saved you a morning of reading, subscribe and share it with one person on your desk. What should the Narrative cover next week? Tell me in the comments.",
    "I'm Anish Pujari, Senior ETRM/CTRM Product Manager & Consultant (Endur, Eka, Triple Point, Azure Databricks). Views my own; prices indicative, not trading advice.",
  ].join("\n\n"),
});

export default function AdminEditorPage() {
  const { id } = useParams();
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyForm);
  const [loaded, setLoaded] = useState(!id);
  const [saving, setSaving] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!user) { navigate("/auth?next=/admin"); return; }
    if (user.role !== "admin") { navigate("/"); return; }
    if (id) {
      api.get(`/admin/posts/${id}`).then((res) => {
        const p = res.data;
        setForm({
          title: p.title,
          excerpt: p.excerpt || "",
          category: p.category,
          tier: p.tier,
          cover_image: p.cover_image || "",
          content: (p.content_blocks || []).join("\n\n"),
          tags: (p.tags || []).join(", "),
          featured: !!p.featured,
          status: p.status,
          publish_at: p.publish_at ? p.publish_at.slice(0, 16) : "",
          edition: p.edition ? String(p.edition) : "",
        });
        setLoaded(true);
      }).catch(() => {
        toast.error("Post not found.");
        navigate("/admin");
      });
    }
  }, [id, user, loading, navigate]);

  const set = (key, val) => setForm((f) => ({ ...f, [key]: val }));

  const applyBriefingTemplate = async () => {
    if (form.title || form.content) {
      if (!window.confirm("This will replace the current title and content with the weekly briefing template. Continue?")) return;
    }
    let nextEdition = 1;
    try {
      const res = await api.get("/admin/posts");
      const editions = (res.data.posts || res.data || []).map((p) => p.edition).filter(Boolean);
      if (editions.length) nextEdition = Math.max(...editions) + 1;
    } catch { /* default to 1 */ }
    setForm((f) => ({ ...f, ...briefingTemplate(nextEdition) }));
    toast.success(`Weekly briefing template loaded — Edition #${nextEdition}. Fill in THE BOARD and the five sections.`);
  };

  const save = async (overrideStatus) => {
    const status = overrideStatus || form.status;
    if (!form.title || form.title.length < 3) { toast.error("Title needs at least 3 characters."); return; }
    if (status === "scheduled" && !form.publish_at) { toast.error("Pick a publish date & time for scheduling."); return; }
    const blocks = form.content.split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean);
    if (status !== "draft" && blocks.length === 0) { toast.error("Add some content before publishing."); return; }
    setSaving(true);
    const payload = {
      title: form.title,
      excerpt: form.excerpt,
      category: form.category,
      tier: form.tier,
      cover_image: form.cover_image,
      content_blocks: blocks,
      tags: form.tags.split(",").map((t) => t.trim()).filter(Boolean),
      featured: form.featured,
      status,
      publish_at: status === "scheduled" && form.publish_at ? new Date(form.publish_at).toISOString() : null,
      edition: form.edition && !isNaN(parseInt(form.edition, 10)) ? parseInt(form.edition, 10) : null,
    };
    try {
      if (id) {
        await api.put(`/admin/posts/${id}`, payload);
      } else {
        await api.post("/admin/posts", payload);
      }
      toast.success(
        status === "published" ? "Post published!" : status === "scheduled" ? "Post scheduled." : "Draft saved."
      );
      navigate("/admin");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed.");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !user || user.role !== "admin" || !loaded) {
    return <div className="container-editorial py-16"><Skeleton className="h-96 rounded-2xl max-w-3xl mx-auto" /></div>;
  }

  return (
    <div className="container-editorial py-10 sm:py-14" data-testid="admin-editor-page">
      <Seo title={id ? "Edit post" : "New post"} path="/admin/editor" />
      <div className="max-w-3xl mx-auto">
        <button onClick={() => navigate("/admin")} className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6" data-testid="admin-editor-back">
          <ArrowLeft className="h-4 w-4" /> Back to Admin Studio
        </button>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-8">
          <h1 className="font-serif text-3xl sm:text-4xl font-semibold">{id ? "Edit post" : "Write a new post"}</h1>
          <Button variant="outline" onClick={applyBriefingTemplate} data-testid="admin-briefing-template-button">
            <LayoutTemplate className="h-4 w-4 mr-2" /> Weekly briefing template
          </Button>
        </div>

        <Card className="rounded-2xl">
          <CardContent className="p-6 sm:p-8 space-y-6">
            <div className="space-y-1.5">
              <Label htmlFor="post-title">Title</Label>
              <Input id="post-title" value={form.title} onChange={(e) => set("title", e.target.value)} placeholder="A headline worth clicking…" className="text-lg h-12 font-serif" data-testid="admin-post-title-input" />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="post-excerpt">Excerpt / dek</Label>
              <Textarea id="post-excerpt" value={form.excerpt} onChange={(e) => set("excerpt", e.target.value)} rows={2} placeholder="One or two sentences that sell the story." data-testid="admin-post-excerpt-input" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Category</Label>
                <Select value={form.category} onValueChange={(v) => set("category", v)}>
                  <SelectTrigger data-testid="admin-post-category-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map((c) => <SelectItem key={c.slug} value={c.slug}>{c.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Tier</Label>
                <Select value={form.tier} onValueChange={(v) => set("tier", v)}>
                  <SelectTrigger data-testid="admin-post-tier-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="free">Free — everyone can read</SelectItem>
                    <SelectItem value="premium">Premium — members only</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="post-tags">Tags <span className="text-muted-foreground font-normal">(comma-separated, max 10)</span></Label>
                <Input id="post-tags" value={form.tags} onChange={(e) => set("tags", e.target.value)} placeholder="AI, Investing, Macro" data-testid="admin-post-tags-input" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="post-edition">Edition # <span className="text-muted-foreground font-normal">(briefings)</span></Label>
                <Input id="post-edition" type="number" min="1" value={form.edition} onChange={(e) => set("edition", e.target.value)} placeholder="e.g. 2" data-testid="admin-post-edition-input" />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="post-cover">Cover image URL</Label>
              <Input id="post-cover" value={form.cover_image} onChange={(e) => set("cover_image", e.target.value)} placeholder="https://images.unsplash.com/…" data-testid="admin-post-cover-input" />
              {form.cover_image && (
                <div className="rounded-lg overflow-hidden border border-border mt-2">
                  <img src={form.cover_image} alt="Cover preview" className="w-full aspect-[16/9] object-cover" onError={(e) => { e.target.style.display = "none"; }} />
                </div>
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="post-content">Content <span className="text-muted-foreground font-normal">(separate paragraphs with a blank line)</span></Label>
                <Button type="button" variant="outline" size="sm" onClick={() => setAiOpen(true)} data-testid="admin-ai-assistant-button">
                  <Wand2 className="h-4 w-4 mr-2 text-accent" /> AI assistant
                </Button>
              </div>
              <Textarea id="post-content" value={form.content} onChange={(e) => set("content", e.target.value)} rows={14} placeholder={"First paragraph…\n\nSecond paragraph…"} className="font-serif text-base leading-7" data-testid="admin-post-content-input" />
              <p className="text-xs text-muted-foreground font-mono">
                {form.content.split(/\n\s*\n/).filter((b) => b.trim()).length} paragraphs · premium posts show the first 3 free
              </p>
            </div>

            <div className="flex items-center justify-between border border-border rounded-lg p-4">
              <div>
                <div className="font-medium text-sm">Featured post</div>
                <div className="text-xs text-muted-foreground">Featured posts headline the homepage hero.</div>
              </div>
              <Switch checked={form.featured} onCheckedChange={(v) => set("featured", v)} data-testid="admin-post-featured-switch" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Status</Label>
                <Select value={form.status} onValueChange={(v) => set("status", v)}>
                  <SelectTrigger data-testid="admin-post-status-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="published">Published</SelectItem>
                    <SelectItem value="scheduled">Scheduled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {form.status === "scheduled" && (
                <div className="space-y-1.5">
                  <Label htmlFor="post-publish-at">Publish at</Label>
                  <Input id="post-publish-at" type="datetime-local" value={form.publish_at} onChange={(e) => set("publish_at", e.target.value)} data-testid="admin-post-schedule-input" />
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Button onClick={() => save()} disabled={saving} className="bg-accent text-accent-foreground hover:bg-accent/90 h-11 flex-1" data-testid="admin-post-save-button">
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                Save {form.status === "draft" ? "draft" : form.status}
              </Button>
              {form.status === "draft" && (
                <Button variant="outline" onClick={() => save("published")} disabled={saving} className="h-11" data-testid="admin-post-publish-button">
                  Publish now
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
        <AiAssistantDialog
          open={aiOpen}
          onOpenChange={setAiOpen}
          content={form.content}
          onReplace={(text) => set("content", text)}
          onAppend={(text) => set("content", form.content ? `${form.content.trimEnd()}\n\n${text}` : text)}
        />
      </div>
    </div>
  );
}
