import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Lock, Clock } from "lucide-react";
import { formatDate } from "@/lib/api";

export const PostCard = ({ post, large = false }) => {
  return (
    <Link
      to={`/post/${post.slug}`}
      className="group block"
      data-testid="article-card"
    >
      <article className="bg-card border border-border rounded-xl overflow-hidden h-full flex flex-col transition-colors duration-200 hover:border-foreground/25">
        <div className={`card-img-zoom overflow-hidden ${large ? "aspect-[16/9]" : "aspect-[3/2]"}`}>
          <img
            src={post.cover_image}
            alt={post.title}
            loading="lazy"
            className="w-full h-full object-cover"
          />
        </div>
        <div className="p-5 flex flex-col flex-1">
          <div className="flex items-center gap-2 mb-3">
            <Badge variant="secondary" className="font-mono text-[10px] uppercase tracking-wider rounded-md">
              {post.category_label}
            </Badge>
            {post.tier === "premium" && (
              <Badge className="bg-accent/10 text-accent border border-accent/30 hover:bg-accent/10 gap-1 rounded-md" data-testid="post-premium-badge">
                <Lock className="h-3 w-3" /> Premium
              </Badge>
            )}
          </div>
          <h3
            className={`font-serif font-semibold leading-snug group-hover:text-accent transition-colors duration-200 ${large ? "text-2xl md:text-3xl" : "text-xl"}`}
            data-testid="article-card-title"
          >
            {post.title}
          </h3>
          <p className="text-muted-foreground text-sm mt-2 line-clamp-2 flex-1">{post.excerpt}</p>
          <div className="flex items-center gap-3 mt-4 text-xs text-muted-foreground font-mono">
            <span>{formatDate(post.published_at)}</span>
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3 w-3" /> {post.read_time} min read
            </span>
          </div>
        </div>
      </article>
    </Link>
  );
};
