import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Search } from "lucide-react";
import { Seo } from "@/components/Seo";
import { PostCard } from "@/components/PostCard";
import { api, CATEGORIES } from "@/lib/api";

export default function ArchivePage() {
  const [posts, setPosts] = useState(null);
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("all");
  const [tier, setTier] = useState("all");
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const params = {};
    if (q) params.q = q;
    if (category !== "all") params.category = category;
    if (tier !== "all") params.tier = tier;
    const t = setTimeout(() => {
      api.get("/posts", { params }).then((res) => {
        setPosts(res.data.posts);
        setTotal(res.data.total);
      }).catch(() => setPosts([]));
    }, 250);
    return () => clearTimeout(t);
  }, [q, category, tier]);

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="archive-page">
      <Seo title="Archive" description="Search and browse every essay published on The Trading Narrative." path="/archive" />
      <span className="section-label">The vault</span>
      <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3">Archive</h1>
      <p className="text-muted-foreground text-lg mt-3">Every narrative we've ever published, searchable.</p>

      <div className="flex flex-col md:flex-row gap-3 mt-8">
        <div className="relative flex-1">
          <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search titles and summaries…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="pl-9 h-11 bg-card"
            data-testid="archive-search-input"
          />
        </div>
        <Select value={category} onValueChange={setCategory}>
          <SelectTrigger className="w-full md:w-52 h-11 bg-card" data-testid="archive-category-filter">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All categories</SelectItem>
            {CATEGORIES.map((c) => (
              <SelectItem key={c.slug} value={c.slug}>{c.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={tier} onValueChange={setTier}>
          <SelectTrigger className="w-full md:w-40 h-11 bg-card" data-testid="archive-tier-filter">
            <SelectValue placeholder="Tier" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All tiers</SelectItem>
            <SelectItem value="free">Free</SelectItem>
            <SelectItem value="premium">Premium</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="text-xs font-mono text-muted-foreground mt-4" data-testid="archive-result-count">
        {posts === null ? "Searching…" : `${total} ${total === 1 ? "essay" : "essays"} found`}
      </div>
      <Separator className="my-6" />

      {posts === null ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">{[...Array(6)].map((_, i) => <Skeleton key={i} className="h-80 rounded-xl" />)}</div>
      ) : posts.length === 0 ? (
        <p className="text-muted-foreground py-12 text-center" data-testid="archive-empty">
          Nothing matches that search. Try different keywords or clear the filters.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" data-testid="archive-posts-grid">
          {posts.map((p) => <PostCard key={p.id} post={p} />)}
        </div>
      )}
    </div>
  );
}
