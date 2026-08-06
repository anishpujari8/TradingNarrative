import { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Bookmark } from "lucide-react";
import { Seo } from "@/components/Seo";
import { PostCard } from "@/components/PostCard";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useBookmarks } from "@/context/BookmarkContext";

export default function ReadingListPage() {
  const { user, loading } = useAuth();
  const { bookmarkedIds } = useBookmarks();
  const navigate = useNavigate();
  const [posts, setPosts] = useState(null);

  const load = useCallback(() => {
    api.get("/bookmarks").then((res) => setPosts(res.data.posts)).catch(() => setPosts([]));
  }, []);

  useEffect(() => {
    if (!loading && !user) {
      navigate("/auth?next=/reading-list");
      return;
    }
    if (user) load();
  }, [user, loading, navigate, load]);

  // refresh list when bookmarks change (e.g., removed via card button)
  useEffect(() => {
    if (user && posts !== null) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookmarkedIds]);

  if (loading || !user) {
    return <div className="container-editorial py-16"><Skeleton className="h-64 rounded-2xl" /></div>;
  }

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="reading-list-page">
      <Seo title="Reading List" description="Essays you've saved for later." path="/reading-list" />
      <span className="section-label">Saved for later</span>
      <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3">Your reading list</h1>
      <p className="text-muted-foreground text-lg mt-3">Every essay you've bookmarked, in one place.</p>
      <Separator className="my-10" />
      {posts === null ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-80 rounded-xl" />)}</div>
      ) : posts.length === 0 ? (
        <div className="text-center py-16" data-testid="reading-list-empty">
          <Bookmark className="h-10 w-10 text-muted-foreground/50 mx-auto mb-4" />
          <h2 className="font-serif text-2xl font-semibold">Nothing saved yet</h2>
          <p className="text-muted-foreground mt-2 mb-6">Tap the bookmark on any essay to build your list.</p>
          <Link to="/archive"><Button className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="reading-list-browse-button">Browse the archive</Button></Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" data-testid="reading-list-grid">
          {posts.map((p) => <PostCard key={p.id} post={p} />)}
        </div>
      )}
    </div>
  );
}
