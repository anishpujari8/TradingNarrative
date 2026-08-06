import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Seo } from "@/components/Seo";
import { PostCard } from "@/components/PostCard";
import { api, CATEGORIES } from "@/lib/api";

export default function CategoryPage() {
  const { slug } = useParams();
  const category = CATEGORIES.find((c) => c.slug === slug);
  const [posts, setPosts] = useState(null);

  useEffect(() => {
    setPosts(null);
    api.get("/posts", { params: { category: slug } })
      .then((res) => setPosts(res.data.posts))
      .catch(() => setPosts([]));
  }, [slug]);

  if (!category) {
    return (
      <div className="container-editorial py-24 text-center">
        <h1 className="font-serif text-3xl font-semibold mb-3">Category not found</h1>
        <Link to="/" className="editorial-link text-accent">Back home</Link>
      </div>
    );
  }

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="category-page">
      <Seo title={category.label} description={category.description} path={`/category/${slug}`} />
      <span className="section-label">Pillar</span>
      <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3" data-testid="category-title">{category.label}</h1>
      <p className="text-muted-foreground text-lg mt-3 max-w-2xl">{category.description}</p>
      <Separator className="my-10" />
      {posts === null ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-80 rounded-xl" />)}</div>
      ) : posts.length === 0 ? (
        <p className="text-muted-foreground py-12" data-testid="category-empty">No posts in this pillar yet. Check back soon.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" data-testid="category-posts-grid">
          {posts.map((p) => <PostCard key={p.id} post={p} />)}
        </div>
      )}
    </div>
  );
}
