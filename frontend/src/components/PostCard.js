import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Lock, Clock } from "lucide-react";
import { formatDate } from "@/lib/api";
import { pillarAccent, withAlpha } from "@/lib/pillars";
import { BookmarkButton } from "@/components/BookmarkButton";

export const PostCard = ({ post, large = false }) => {
  const accent = pillarAccent(post.category);
  return (
    <Link
      to={`/post/${post.slug}`}
      className="group block"
      data-testid="article-card"
    >
      <article
        className="bg-card border rounded-xl overflow-hidden h-full flex flex-col transition-[border-color,box-shadow] duration-200"
        style={{ borderColor: withAlpha(accent, 0.32), "--pillar-accent": accent }}
        onMouseEnter={(e) => { e.currentTarget.style.borderColor = withAlpha(accent, 0.7); }}
        onMouseLeave={(e) => { e.currentTarget.style.borderColor = withAlpha(accent, 0.32); }}
      >
        <div className={`relative card-img-zoom overflow-hidden ${large ? "aspect-[16/9]" : "aspect-[3/2]"}`}>
          <BookmarkButton postId={post.id} variant="overlay" />
          <img
            src={post.cover_image}
            alt={post.title}
            loading="lazy"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-x-0 bottom-0 h-[3px]" style={{ backgroundColor: accent }} aria-hidden />
        </div>
        <div className="p-5 flex flex-col flex-1">
          <div className="flex items-center gap-2 mb-3">
            <Badge
              className="font-mono text-[10px] uppercase tracking-wider rounded-md border"
              style={{ backgroundColor: withAlpha(accent, 0.12), color: accent, borderColor: withAlpha(accent, 0.3) }}
              data-testid="post-category-badge"
            >
              {post.category_label}
            </Badge>
            {post.edition && (
              <Badge className="bg-primary/10 text-primary border border-primary/20 hover:bg-primary/10 font-mono text-[10px] rounded-md" data-testid="post-edition-badge">
                #{post.edition}
              </Badge>
            )}
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
