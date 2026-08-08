import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Star } from "lucide-react";
import { api } from "@/lib/api";

/** Public thank-you wall for Founding Members, shown on the About page. */
export const FoundingWall = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/founding-members").then((r) => setData(r.data)).catch(() => setData({ members: [] }));
  }, []);

  if (!data) return null;

  return (
    <section className="mt-14" data-testid="founding-wall">
      <div className="flex items-center gap-2.5">
        <Star className="h-5 w-5 text-accent" />
        <h2 className="font-serif text-3xl font-semibold">Founding Members</h2>
      </div>
      <p className="text-muted-foreground mt-2 max-w-2xl">
        The readers who backed The Trading Narrative early — before it was proven. Every essay,
        briefing, and narration exists in part because of them.
      </p>

      {data.members.length === 0 ? (
        <div className="mt-6 border border-dashed border-accent/40 bg-accent/5 rounded-2xl p-8 text-center" data-testid="founding-wall-empty">
          <p className="font-serif text-xl">This wall is waiting for its first name.</p>
          <p className="text-sm text-muted-foreground mt-2 mb-5">
            Become a Founding Member and your name lives here permanently — along with direct
            access to Anish and the quarterly members call.
          </p>
          <Link to="/pricing">
            <Button className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="founding-wall-cta">
              <Star className="h-4 w-4 mr-2" /> Become a Founding Member
            </Button>
          </Link>
        </div>
      ) : (
        <>
          <div className="mt-6 flex flex-wrap gap-3" data-testid="founding-wall-members">
            {data.members.map((m) => (
              <div
                key={`${m.name}-${m.since}`}
                className="flex items-center gap-2.5 border border-accent/30 bg-accent/5 rounded-full pl-2 pr-4 py-1.5"
                data-testid="founding-wall-member"
              >
                <span className="h-8 w-8 rounded-full bg-accent/15 text-accent flex items-center justify-center font-serif font-semibold">
                  {m.name.charAt(0).toUpperCase()}
                </span>
                <div className="leading-tight">
                  <div className="text-sm font-medium">{m.name}</div>
                  {m.since && <div className="text-[10px] text-muted-foreground font-mono">since {m.since}</div>}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-5 flex items-center gap-3">
            <Badge variant="secondary" className="font-mono">{data.count} founding member{data.count === 1 ? "" : "s"}</Badge>
            <Link to="/pricing" className="text-sm text-accent hover:underline" data-testid="founding-wall-join-link">
              Add your name →
            </Link>
          </div>
        </>
      )}
    </section>
  );
};
