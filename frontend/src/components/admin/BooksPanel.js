import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Pencil, Trash2, Plus, BookOpen } from "lucide-react";
import { api } from "@/lib/api";

const EMPTY = { title: "", author: "Anish Pujari", description: "", cover_image: "", buy_url: "", featured: false, sort: 0, related_slug: "", related_title: "" };

// Admin bookshelf manager: add/edit/delete the recommendations shown at /books.
export const BooksPanel = () => {
  const [books, setBooks] = useState([]);
  const [posts, setPosts] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = () => api.get("/books").then((r) => setBooks(r.data.books)).catch(() => {});
  useEffect(() => {
    load();
    api.get("/posts?limit=100").then((r) => setPosts(r.data.posts || [])).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e?.target ? e.target.value : e });

  const save = async () => {
    if (!form.title.trim() || !form.author.trim() || !form.buy_url.trim()) {
      toast.error("Title, author, and buy link are required");
      return;
    }
    setSaving(true);
    try {
      if (editingId) {
        await api.put(`/admin/books/${editingId}`, { ...form, sort: Number(form.sort) || 0 });
        toast.success("Book updated");
      } else {
        await api.post("/admin/books", { ...form, sort: Number(form.sort) || 0 });
        toast.success("Book added to the shelf");
      }
      setForm(EMPTY);
      setEditingId(null);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not save the book");
    } finally {
      setSaving(false);
    }
  };

  const edit = (b) => {
    setEditingId(b.id);
    setForm({ title: b.title, author: b.author, description: b.description || "", cover_image: b.cover_image || "", buy_url: b.buy_url, featured: !!b.featured, sort: b.sort || 0, related_slug: b.related_slug || "", related_title: b.related_title || "" });
  };

  const remove = async (b) => {
    if (!window.confirm(`Remove "${b.title}" from the shelf?`)) return;
    try {
      await api.delete(`/admin/books/${b.id}`);
      toast.success("Book removed");
      if (editingId === b.id) { setEditingId(null); setForm(EMPTY); }
      load();
    } catch {
      toast.error("Could not remove the book");
    }
  };

  return (
    <div className="grid lg:grid-cols-2 gap-6" data-testid="admin-books-panel">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-serif flex items-center gap-2">
            <Plus className="h-4 w-4" /> {editingId ? "Edit book" : "Add a book"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label>Title</Label>
            <Input value={form.title} onChange={set("title")} placeholder="Book title" data-testid="admin-book-title-input" />
          </div>
          <div className="space-y-1.5">
            <Label>Author</Label>
            <Input value={form.author} onChange={set("author")} placeholder="Author name" data-testid="admin-book-author-input" />
          </div>
          <div className="space-y-1.5">
            <Label>Short description</Label>
            <Textarea value={form.description} onChange={set("description")} rows={4} placeholder="Why this book earns its spot on the shelf" data-testid="admin-book-description-input" />
          </div>
          <div className="space-y-1.5">
            <Label>Cover image URL</Label>
            <Input value={form.cover_image} onChange={set("cover_image")} placeholder="https://... or /book-cover.webp" data-testid="admin-book-cover-input" />
          </div>
          <div className="space-y-1.5">
            <Label>Buy link (Amazon)</Label>
            <Input value={form.buy_url} onChange={set("buy_url")} placeholder="https://www.amazon.in/dp/..." data-testid="admin-book-buyurl-input" />
          </div>
          <div className="space-y-1.5">
            <Label>Reading Notes essay (optional)</Label>
            <Select
              value={form.related_slug || "none"}
              onValueChange={(v) => {
                if (v === "none") {
                  setForm({ ...form, related_slug: "", related_title: "" });
                } else {
                  const p = posts.find((x) => x.slug === v);
                  setForm({ ...form, related_slug: v, related_title: p?.title || "" });
                }
              }}
            >
              <SelectTrigger data-testid="admin-book-related-select">
                <SelectValue placeholder="Link a related essay" />
              </SelectTrigger>
              <SelectContent className="max-h-72">
                <SelectItem value="none">No linked essay</SelectItem>
                {posts.map((p) => (
                  <SelectItem key={p.slug} value={p.slug}>{p.title}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">Adds a "Reading Notes" link on the book card pointing to your essay.</p>
          </div>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Switch checked={form.featured} onCheckedChange={(v) => setForm({ ...form, featured: v })} data-testid="admin-book-featured-switch" />
              <Label className="text-sm text-muted-foreground">Featured ("By the author" badge, shown first)</Label>
            </div>
            <div className="flex items-center gap-2">
              <Label className="text-sm text-muted-foreground">Sort</Label>
              <Input type="number" className="w-20" value={form.sort} onChange={set("sort")} data-testid="admin-book-sort-input" />
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={save} disabled={saving} data-testid="admin-book-save-btn">
              {saving ? "Saving…" : editingId ? "Update book" : "Add book"}
            </Button>
            {editingId && (
              <Button variant="outline" onClick={() => { setEditingId(null); setForm(EMPTY); }} data-testid="admin-book-cancel-btn">
                Cancel
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-serif flex items-center gap-2">
            <BookOpen className="h-4 w-4" /> On the shelf ({books.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {books.length === 0 && <p className="text-sm text-muted-foreground">No books yet, add the first one.</p>}
          {books.map((b) => (
            <div key={b.id} className="flex items-center gap-3 border border-border rounded-lg p-3" data-testid={`admin-book-row-${b.id}`}>
              {b.cover_image ? (
                <img src={b.cover_image} alt={b.title} className="h-14 w-11 object-cover rounded shrink-0" />
              ) : (
                <div className="h-14 w-11 bg-muted rounded flex items-center justify-center shrink-0"><BookOpen className="h-4 w-4 text-muted-foreground" /></div>
              )}
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium truncate">{b.title}{b.featured ? " ★" : ""}</div>
                <div className="text-xs text-muted-foreground truncate">by {b.author}</div>
                {b.related_title && (
                  <div className="text-xs text-accent truncate" data-testid={`admin-book-related-${b.id}`}>Notes: {b.related_title}</div>
                )}
              </div>
              <Button size="icon" variant="ghost" onClick={() => edit(b)} aria-label={`Edit ${b.title}`} data-testid={`admin-book-edit-${b.id}`}>
                <Pencil className="h-4 w-4" />
              </Button>
              <Button size="icon" variant="ghost" className="text-destructive" onClick={() => remove(b)} aria-label={`Delete ${b.title}`} data-testid={`admin-book-delete-${b.id}`}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};
