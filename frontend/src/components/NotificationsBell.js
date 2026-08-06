import { useEffect, useState, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Bell, MessageCircle, MessagesSquare } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const timeAgo = (iso) => {
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};

export const NotificationsBell = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);

  const load = useCallback(() => {
    if (!user) return;
    api.get("/notifications")
      .then((res) => {
        setItems(res.data.notifications);
        setUnread(res.data.unread);
      })
      .catch(() => {});
  }, [user]);

  useEffect(() => {
    load();
    const t = setInterval(load, 60000);
    return () => clearInterval(t);
  }, [load, location.pathname]);

  if (!user) return null;

  const onOpenChange = (open) => {
    if (open && unread > 0) {
      api.post("/notifications/mark-read").then(() => setUnread(0)).catch(() => {});
    }
  };

  return (
    <DropdownMenu onOpenChange={onOpenChange}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" data-testid="notifications-bell" aria-label="Notifications">
          <Bell className="h-4 w-4" />
          {unread > 0 && (
            <span className="absolute top-1 right-1 min-w-[16px] h-4 px-1 rounded-full bg-accent text-accent-foreground text-[10px] font-semibold flex items-center justify-center" data-testid="notifications-badge">
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 p-0">
        <div className="px-4 py-3 border-b border-border font-serif font-semibold">Notifications</div>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground p-4" data-testid="notifications-empty">
            No notifications yet. When someone replies to your comment, it shows up here.
          </p>
        ) : (
          <div className="max-h-96 overflow-y-auto" data-testid="notifications-list">
            {items.map((n) => (
              <button
                key={n.id}
                onClick={() => navigate(n.type === "lounge_reply" ? `/lounge?thread=${n.thread_id}` : `/post/${n.post_slug}`)}
                className={`w-full text-left px-4 py-3 border-b border-border last:border-0 hover:bg-muted/50 transition-colors ${!n.read ? "bg-accent/5" : ""}`}
                data-testid="notification-item"
              >
                <div className="flex items-start gap-2.5">
                  {n.type === "lounge_reply" ? (
                    <MessagesSquare className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                  ) : (
                    <MessageCircle className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                  )}
                  <div className="min-w-0">
                    <p className="text-sm">
                      {n.type === "lounge_reply" ? (
                        <>
                          <span className="font-medium">{n.actor_name}</span> replied in your Lounge discussion{" "}
                          <span className="font-medium">"{n.thread_title}"</span>
                        </>
                      ) : (
                        <>
                          <span className="font-medium">{n.actor_name}</span> replied to your comment on{" "}
                          <span className="font-medium">"{n.post_title}"</span>
                        </>
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{n.preview}</p>
                    <p className="text-[10px] text-muted-foreground font-mono mt-1">{timeAgo(n.created_at)}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
