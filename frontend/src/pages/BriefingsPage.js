import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Lock, Clock, ArrowRight, Newspaper, Sparkles } from "lucide-react";
import { Seo } from "@/components/Seo";
import { api, formatDate, SITE_URL } from "@/lib/api";
import { pillarAccent, withAlpha, PillarMotif, pillarMascot, PILLAR_MASCOT_ALTS } from "@/lib/pillars";

const ACCENT = pillarAccent("briefings");

export default function BriefingsPage() {
  const [briefings, setBriefings] = useState(null);

  useEffect(() => {
    api.get("/briefings").then((r) => setBriefings(r.data.briefings)).catch(() => setBriefings([]));
  }, []);

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="briefings-page">
      <Seo
        title="The Weekly Briefing · Commodity Trading & Freight Newsletter"
        description="The Weekly Briefing is a free trading newsletter: commodity desks, freight and shipping markets, energy and metals, risk and regulation, in five minutes every Wednesday."
        keywords="weekly briefing, newsletter, trading, freight, commodity trading, shipping, markets, risk, regulation"
        path="/briefings"
        image={`${SITE_URL}/api/og/page/briefings.png`}
      />
      <div
        className="relative overflow-hidden rounded-2xl border px-6 sm:px-10 py-8 sm:py-10"
        style={{ borderColor: withAlpha(ACCENT, 0.35), backgroundColor: withAlpha(ACCENT, 0.07) }}
        data-testid="briefings-header-banner"
      >
        <div className="absolute inset-y-0 right-0 w-3/4 sm:w-1/2 pointer-events-none" style={{ color: ACCENT, opacity: 0.16 }}>
          <PillarMotif category="briefings" className="h-full w-full" />
        </div>
        <div className="relative flex items-center gap-6 sm:gap-10">
          <div className="min-w-0 flex-1">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em]" style={{ color: ACCENT }}>The series</span>
            <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3 leading-tight">The Weekly Briefing</h1>
            <p className="text-muted-foreground leading-relaxed mt-4 max-w-2xl">
              Five things that actually change how trading and risk teams work, every week,
              written the way a desk reads them. Follow the editions in order or jump to the latest.
            </p>
            <div className="h-1 w-16 rounded-full mt-5" style={{ backgroundColor: ACCENT }} aria-hidden />
          </div>
          <img
            src={pillarMascot("briefings")}
            alt={PILLAR_MASCOT_ALTS.briefings}
            className="h-20 w-20 sm:h-32 sm:w-32 lg:h-40 lg:w-40 rounded-full object-cover shrink-0 shadow-lg"
            style={{ border: `3px solid ${withAlpha(ACCENT, 0.55)}` }}
            loading="lazy"
            data-testid="briefings-mascot"
          />
        </div>
      </div>

      <div className="mt-10 max-w-3xl space-y-4">
        {briefings && briefings.length > 0 && Math.max(...briefings.map((b) => b.edition || 0)) <= 6 && (
          <Card className="rounded-xl border-accent/40 bg-accent/5" data-testid="briefings-free-banner">
            <CardContent className="p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 font-medium">
                  <Sparkles className="h-4 w-4 text-accent shrink-0" />
                  <span data-testid="briefings-free-banner-title">Free through Edition #6</span>
                </div>
                <p className="text-sm text-muted-foreground mt-1" data-testid="briefings-free-banner-copy">
                  {(() => {
                    const remaining = 6 - Math.max(...briefings.map((b) => b.edition || 0));
                    return remaining > 0
                      ? `${remaining} free ${remaining === 1 ? "edition remains" : "editions remain"}, from Edition #7 the briefing is premium-only. Subscribe before the paywall.`
                      : "This is the last free edition, from Edition #7 the briefing is premium-only. Subscribe before the paywall.";
                  })()}
                </p>
              </div>
              <Link
                to="/pricing"
                className="inline-flex items-center justify-center gap-1.5 shrink-0 h-10 px-4 rounded-md bg-accent text-accent-foreground text-sm font-medium hover:bg-accent/90 transition-colors"
                data-testid="briefings-free-banner-cta"
              >
                Go Premium early <ArrowRight className="h-4 w-4" />
              </Link>
            </CardContent>
          </Card>
        )}
        {briefings === null ? (
          <>
            <Skeleton className="h-32 rounded-xl" />
            <Skeleton className="h-32 rounded-xl" />
          </>
        ) : briefings.length === 0 ? (
          <Card className="rounded-xl">
            <CardContent className="py-16 text-center" data-testid="briefings-empty">
              <Newspaper className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
              <h3 className="font-serif text-xl font-semibold mb-2">No editions yet</h3>
              <p className="text-sm text-muted-foreground">The first briefing lands here soon.</p>
            </CardContent>
          </Card>
        ) : (
          briefings.map((b) => (
            <Link key={b.id} to={`/post/${b.slug}`} className="block group" data-testid={`briefing-card-${b.edition}`}>
              <Card className="rounded-xl transition-colors duration-150 hover:border-accent/40">
                <CardContent className="p-5 sm:p-6 flex items-start gap-5">
                  <div className="w-14 h-14 rounded-xl bg-primary/5 border border-primary/15 flex flex-col items-center justify-center shrink-0">
                    <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground">Edition</span>
                    <span className="text-xl font-semibold text-primary leading-none">#{b.edition}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <span className="text-[11px] font-mono text-muted-foreground">{formatDate(b.published_at)}</span>
                      <span className="text-[11px] font-mono text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" /> {b.read_time} min
                      </span>
                      {b.tier === "premium" && (
                        <Badge className="bg-accent/10 text-accent border-accent/30 hover:bg-accent/10 gap-1 text-[10px] px-1.5 py-0">
                          <Lock className="h-3 w-3" /> Premium
                        </Badge>
                      )}
                    </div>
                    <h2 className="font-serif text-xl font-semibold leading-snug group-hover:text-accent transition-colors">
                      {b.title}
                    </h2>
                    <p className="text-sm text-muted-foreground line-clamp-2 mt-1.5">{b.excerpt}</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-accent group-hover:translate-x-0.5 transition-all shrink-0 self-center" />
                </CardContent>
              </Card>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
