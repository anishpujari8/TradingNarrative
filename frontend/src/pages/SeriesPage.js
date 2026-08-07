import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Layers, ArrowRight } from "lucide-react";
import { Seo } from "@/components/Seo";
import { PostCard } from "@/components/PostCard";
import { api } from "@/lib/api";

export default function SeriesPage() {
  const { slug } = useParams();
  const [series, setSeries] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    setSeries(null);
    setError(false);
    api.get(`/series/${slug}`)
      .then((res) => setSeries(res.data))
      .catch(() => setError(true));
    window.scrollTo(0, 0);
  }, [slug]);

  if (error) {
    return (
      <div className="container-editorial py-24 text-center" data-testid="series-not-found">
        <h1 className="font-serif text-3xl font-semibold">Series not found</h1>
        <p className="text-muted-foreground mt-3 mb-6">This collection doesn't exist (yet).</p>
        <Link to="/archive"><Button variant="outline" data-testid="series-back-button">Browse all essays</Button></Link>
      </div>
    );
  }

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="series-page">
      {!series ? (
        <div className="space-y-6">
          <Skeleton className="h-10 w-1/2" />
          <Skeleton className="h-5 w-2/3" />
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-72 rounded-2xl" />)}
          </div>
        </div>
      ) : (
        <>
          <Seo title={`${series.title} — Series`} description={series.description} path={`/series/${series.slug}`} />
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-accent" />
            <span className="section-label">Series</span>
          </div>
          <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3" data-testid="series-title">{series.title}</h1>
          <p className="text-muted-foreground text-lg mt-4 max-w-2xl" data-testid="series-description">{series.description}</p>
          <div className="mt-4">
            <Badge variant="secondary" className="font-mono text-[11px]" data-testid="series-count-badge">
              {series.count} essay{series.count === 1 ? "" : "s"} and counting
            </Badge>
          </div>
          <Separator className="my-10" />

          <div className="space-y-8" data-testid="series-post-list">
            {series.posts.map((p, i) => (
              <div key={p.slug} className="flex gap-5 items-start" data-testid={`series-item-${i + 1}`}>
                <div className="font-serif text-4xl font-semibold text-accent/30 leading-none pt-1 w-12 shrink-0 select-none">
                  {String(i + 1).padStart(2, "0")}
                </div>
                <div className="flex-1 min-w-0">
                  <PostCard post={p} />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <Link to="/archive">
              <Button variant="outline" data-testid="series-browse-all">
                Browse all essays <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
