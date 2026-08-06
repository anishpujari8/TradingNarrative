import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Bookmark } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { useBookmarks } from "@/context/BookmarkContext";

export const BookmarkButton = ({ postId, variant = "icon", className = "" }) => {
  const { user } = useAuth();
  const { bookmarkedIds, toggle } = useBookmarks();
  const navigate = useNavigate();
  const location = useLocation();
  const saved = bookmarkedIds.has(postId);

  const onClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!user) {
      toast.info("Sign in to save essays to your reading list.");
      navigate(`/auth?next=${encodeURIComponent(location.pathname)}`);
      return;
    }
    toggle(postId);
  };

  if (variant === "overlay") {
    return (
      <button
        onClick={onClick}
        aria-label={saved ? "Remove bookmark" : "Save to reading list"}
        className={`absolute top-3 right-3 z-10 p-2 rounded-full backdrop-blur-md transition-colors duration-150 ${saved ? "bg-accent text-accent-foreground" : "bg-black/40 text-white hover:bg-black/60"} ${className}`}
        data-testid="bookmark-overlay-button"
      >
        <Bookmark className="h-4 w-4" fill={saved ? "currentColor" : "none"} />
      </button>
    );
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onClick}
      className={`gap-1.5 ${saved ? "border-accent/50 text-accent hover:text-accent" : ""} ${className}`}
      data-testid="bookmark-button"
    >
      <Bookmark className="h-4 w-4" fill={saved ? "currentColor" : "none"} />
      {saved ? "Saved" : "Save"}
    </Button>
  );
};
