import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const BookmarkContext = createContext(null);

export const BookmarkProvider = ({ children }) => {
  const { user } = useAuth();
  const [ids, setIds] = useState(new Set());

  useEffect(() => {
    if (!user) {
      setIds(new Set());
      return;
    }
    api.get("/bookmarks")
      .then((res) => setIds(new Set(res.data.post_ids)))
      .catch(() => {});
  }, [user]);

  const toggle = useCallback(async (postId) => {
    try {
      const res = await api.post("/bookmarks/toggle", { post_id: postId });
      setIds((prev) => {
        const next = new Set(prev);
        if (res.data.bookmarked) next.add(postId);
        else next.delete(postId);
        return next;
      });
      toast.success(res.data.bookmarked ? "Saved to your reading list." : "Removed from your reading list.");
      return res.data.bookmarked;
    } catch {
      toast.error("Could not update your reading list.");
      return null;
    }
  }, []);

  return (
    <BookmarkContext.Provider value={{ bookmarkedIds: ids, toggle }}>
      {children}
    </BookmarkContext.Provider>
  );
};

export const useBookmarks = () => useContext(BookmarkContext);
