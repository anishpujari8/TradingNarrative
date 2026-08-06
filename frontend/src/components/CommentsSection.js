import { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { MessageCircle, Trash2, Crown, Loader2, Lock } from "lucide-react";
import { toast } from "sonner";
import { api, formatDate } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export const CommentsSection = ({ post }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [comments, setComments] = useState(null);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.get(`/posts/${post.slug}/comments`).then((res) => setComments(res.data.comments)).catch(() => setComments([]));
  }, [post.slug]);

  useEffect(() => { load(); }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    if (!body.trim()) return;
    setBusy(true);
    try {
      await api.post(`/posts/${post.slug}/comments`, { body: body.trim() });
      setBody("");
      toast.success("Comment posted.");
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not post your comment.");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    try {
      await api.delete(`/comments/${id}`);
      toast.success("Comment deleted.");
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed.");
    }
  };

  const canComment = user && (user.is_premium || user.role === "admin");

  return (
    <section className="mt-12" data-testid="comments-section">
      <div className="flex items-center gap-2 mb-6">
        <MessageCircle className="h-5 w-5 text-accent" />
        <h2 className="font-serif text-2xl font-semibold">
          Member discussion {comments !== null && <span className="text-muted-foreground font-sans text-base">({comments.length})</span>}
        </h2>
      </div>

      {/* Composer / gate */}
      {canComment ? (
        <form onSubmit={submit} className="mb-8" data-testid="comment-form">
          <Textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={3}
            maxLength={2000}
            placeholder="Share your take — what resonated, what didn't?"
            className="bg-card"
            data-testid="comment-input"
          />
          <div className="flex items-center justify-between mt-3">
            <span className="text-xs text-muted-foreground font-mono">{body.length}/2000</span>
            <Button type="submit" disabled={busy || !body.trim()} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="comment-submit-button">
              {busy && <Loader2 className="h-4 w-4 animate-spin mr-2" />} Post comment
            </Button>
          </div>
        </form>
      ) : (
        <div className="bg-muted/40 border border-border rounded-xl p-6 mb-8 flex flex-col sm:flex-row items-start sm:items-center gap-4 justify-between" data-testid="comment-gate">
          <div className="flex items-start gap-3">
            <Lock className="h-5 w-5 text-accent mt-0.5 shrink-0" />
            <div>
              <div className="font-medium text-sm">The discussion is a Premium member perk</div>
              <div className="text-xs text-muted-foreground mt-0.5">
                {user ? "Upgrade to join the conversation with other members." : "Sign in and go Premium to join the conversation."}
              </div>
            </div>
          </div>
          <Button
            onClick={() => navigate(user ? "/pricing" : `/auth?next=/post/${post.slug}`)}
            className="bg-accent text-accent-foreground hover:bg-accent/90 shrink-0"
            data-testid="comment-gate-cta"
          >
            <Crown className="h-4 w-4 mr-2" /> {user ? "Go Premium" : "Sign in"}
          </Button>
        </div>
      )}

      {/* List */}
      {comments === null ? (
        <div className="space-y-4">{[...Array(2)].map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>
      ) : comments.length === 0 ? (
        <p className="text-sm text-muted-foreground" data-testid="comments-empty">
          No comments yet — be the first to share your perspective.
        </p>
      ) : (
        <div className="space-y-5" data-testid="comments-list">
          {comments.map((c) => (
            <div key={c.id} className="flex gap-3" data-testid="comment-item">
              <Avatar className="h-9 w-9 border border-border shrink-0">
                <AvatarFallback className="bg-secondary text-xs font-medium">
                  {(c.user_name || "?").slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-sm">{c.user_name}</span>
                  {c.is_admin && (
                    <Badge className="bg-accent/10 text-accent border border-accent/30 hover:bg-accent/10 text-[10px] py-0">Author</Badge>
                  )}
                  <span className="text-xs text-muted-foreground font-mono">{formatDate(c.created_at)}</span>
                  {user && (user.id === c.user_id || user.role === "admin") && (
                    <button
                      onClick={() => remove(c.id)}
                      className="text-muted-foreground hover:text-destructive transition-colors ml-auto"
                      aria-label="Delete comment"
                      data-testid="comment-delete-button"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
                <p className="text-sm text-foreground/90 mt-1 whitespace-pre-wrap break-words">{c.body}</p>
              </div>
            </div>
          ))}
        </div>
      )}
      {!user && comments?.length > 0 && (
        <p className="text-xs text-muted-foreground mt-6">
          <Link to={`/auth?next=/post/${post.slug}`} className="editorial-link text-accent">Sign in</Link> to join the discussion.
        </p>
      )}
    </section>
  );
};
