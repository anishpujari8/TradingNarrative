import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Headphones, IndianRupee, DollarSign, Rocket, Search, Plus, Trash2, TrendingUp, TrendingDown, Minus, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api, formatINR } from "@/lib/api";

// The six head terms the site is tuned for (see SEO.md)
const TARGET_KEYWORDS = ["trading", "freight", "business and finance", "narrative", "weekly briefing", "newsletter"];

const Delta = ({ latest, previous, invert = false }) => {
  if (previous === null || previous === undefined || latest === null || latest === undefined) {
    return <Minus className="h-3 w-3 text-muted-foreground/50 inline" aria-label="no previous data" />;
  }
  const diff = latest - previous;
  if (diff === 0) return <Minus className="h-3 w-3 text-muted-foreground/50 inline" aria-label="unchanged" />;
  const good = invert ? diff < 0 : diff > 0;
  const Icon = diff > 0 ? TrendingUp : TrendingDown;
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs font-mono ${good ? "text-accent" : "text-destructive"}`}>
      <Icon className="h-3 w-3" />
      {diff > 0 ? "+" : ""}{Number.isInteger(diff) ? diff : diff.toFixed(1)}
    </span>
  );
};

export const GrowthPanel = () => {
  const [sales, setSales] = useState(null);
  const [earlyBird, setEarlyBird] = useState(null);
  const [seo, setSeo] = useState(null);
  const [kw, setKw] = useState("");
  const [impressions, setImpressions] = useState("");
  const [clicks, setClicks] = useState("");
  const [position, setPosition] = useState("");
  const [notedOn, setNotedOn] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    api.get("/admin/audio-sales").then((r) => setSales(r.data)).catch(() => setSales({ total_purchases: 0, revenue_inr: 0, revenue_usd: 0, best_sellers: [], recent: [] }));
    api.get("/billing/early-bird").then((r) => setEarlyBird(r.data)).catch(() => {});
    api.get("/admin/seo/keywords").then((r) => setSeo(r.data.keywords)).catch(() => setSeo([]));
  }, []);

  useEffect(() => { load(); }, [load]);

  const addEntry = async () => {
    if (!kw.trim()) { toast.error("Pick or type a keyword first."); return; }
    if (impressions === "" || clicks === "") { toast.error("Impressions and clicks are required."); return; }
    setSaving(true);
    try {
      await api.post("/admin/seo/keywords", {
        keyword: kw.trim(),
        impressions: parseInt(impressions, 10) || 0,
        clicks: parseInt(clicks, 10) || 0,
        position: position === "" ? null : parseFloat(position),
        noted_on: notedOn || null,
      });
      toast.success(`Logged "${kw.trim()}" numbers.`);
      setImpressions(""); setClicks(""); setPosition("");
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not save the entry.");
    } finally {
      setSaving(false);
    }
  };

  const deleteEntry = async (entryId, keyword) => {
    try {
      await api.delete(`/admin/seo/keywords/${entryId}`);
      toast.success(`Removed latest "${keyword}" entry.`);
      load();
    } catch {
      toast.error("Could not delete the entry.");
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-growth-panel">
      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="rounded-2xl" data-testid="growth-audio-count-card">
          <CardContent className="pt-5">
            <div className="flex items-center gap-2 text-xs text-muted-foreground"><Headphones className="h-3.5 w-3.5 text-accent" /> Narration unlocks</div>
            {sales === null ? <Skeleton className="h-8 w-16 mt-2" /> :
              <div className="text-3xl font-semibold mt-1" data-testid="growth-audio-count">{sales.total_purchases}</div>}
          </CardContent>
        </Card>
        <Card className="rounded-2xl" data-testid="growth-revenue-inr-card">
          <CardContent className="pt-5">
            <div className="flex items-center gap-2 text-xs text-muted-foreground"><IndianRupee className="h-3.5 w-3.5 text-accent" /> Audio revenue (Razorpay)</div>
            {sales === null ? <Skeleton className="h-8 w-20 mt-2" /> :
              <div className="text-3xl font-semibold mt-1" data-testid="growth-revenue-inr">{formatINR(sales.revenue_inr)}</div>}
          </CardContent>
        </Card>
        <Card className="rounded-2xl" data-testid="growth-revenue-usd-card">
          <CardContent className="pt-5">
            <div className="flex items-center gap-2 text-xs text-muted-foreground"><DollarSign className="h-3.5 w-3.5 text-accent" /> Audio revenue (Stripe)</div>
            {sales === null ? <Skeleton className="h-8 w-20 mt-2" /> :
              <div className="text-3xl font-semibold mt-1" data-testid="growth-revenue-usd">${sales.revenue_usd.toFixed(2)}</div>}
          </CardContent>
        </Card>
        <Card className="rounded-2xl" data-testid="growth-early-bird-card">
          <CardContent className="pt-5">
            <div className="flex items-center gap-2 text-xs text-muted-foreground"><Rocket className="h-3.5 w-3.5 text-accent" /> Early bird claims</div>
            {earlyBird === null ? <Skeleton className="h-8 w-20 mt-2" /> : (
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-semibold" data-testid="growth-early-bird-claimed">{earlyBird.claimed}</span>
                <span className="text-sm text-muted-foreground">of {earlyBird.spots}</span>
                {earlyBird.active
                  ? <Badge className="bg-accent/10 text-accent border border-accent/30 hover:bg-accent/10 text-[10px]">live</Badge>
                  : <Badge variant="secondary" className="text-[10px]">ended</Badge>}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Best sellers */}
        <Card className="rounded-2xl" data-testid="growth-best-sellers-card">
          <CardHeader className="pb-2">
            <CardTitle className="font-serif text-xl flex items-center gap-2"><Headphones className="h-5 w-5 text-accent" /> Best-selling narrations</CardTitle>
          </CardHeader>
          <CardContent>
            {sales === null ? <Skeleton className="h-24" /> : sales.best_sellers.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4" data-testid="growth-best-sellers-empty">
                No narration purchases yet. When readers start unlocking audio for ₹45, the best sellers show up here.
              </p>
            ) : (
              <Table data-testid="growth-best-sellers-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Essay</TableHead>
                    <TableHead className="text-right">Sold</TableHead>
                    <TableHead className="text-right">₹</TableHead>
                    <TableHead className="text-right">$</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sales.best_sellers.map((s) => (
                    <TableRow key={s.slug}>
                      <TableCell className="text-sm max-w-[220px] truncate">{s.title}</TableCell>
                      <TableCell className="text-right font-mono text-sm">{s.purchases}</TableCell>
                      <TableCell className="text-right font-mono text-sm">{formatINR(s.revenue_inr)}</TableCell>
                      <TableCell className="text-right font-mono text-sm">${s.revenue_usd.toFixed(2)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Recent purchases */}
        <Card className="rounded-2xl" data-testid="growth-recent-purchases-card">
          <CardHeader className="pb-2">
            <CardTitle className="font-serif text-xl">Recent narration purchases</CardTitle>
          </CardHeader>
          <CardContent>
            {sales === null ? <Skeleton className="h-24" /> : sales.recent.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4" data-testid="growth-recent-empty">No purchases yet.</p>
            ) : (
              <Table data-testid="growth-recent-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Buyer</TableHead>
                    <TableHead>Essay</TableHead>
                    <TableHead className="text-right">Paid</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sales.recent.map((r, i) => (
                    <TableRow key={i}>
                      <TableCell className="text-sm max-w-[140px] truncate">{r.email || "—"}</TableCell>
                      <TableCell className="text-sm max-w-[180px] truncate">{r.title}</TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        {r.currency === "INR" ? formatINR(r.amount) : `$${Number(r.amount).toFixed(2)}`}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Search rank tracker */}
      <Card className="rounded-2xl" data-testid="growth-rank-tracker-card">
        <CardHeader className="pb-2">
          <CardTitle className="font-serif text-xl flex items-center gap-2"><Search className="h-5 w-5 text-accent" /> Search rank tracker</CardTitle>
          <p className="text-xs text-muted-foreground">
            Paste your Google Search Console numbers here whenever you check them. Deltas compare each keyword's latest entry with the one before.
          </p>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-1.5 mb-4" data-testid="growth-keyword-chips">
            {TARGET_KEYWORDS.map((k) => (
              <button
                key={k}
                onClick={() => setKw(k)}
                className={`px-3 py-1 rounded-full text-xs border transition-colors ${kw === k ? "bg-accent text-accent-foreground border-accent" : "border-border text-muted-foreground hover:border-accent/50 hover:text-foreground"}`}
                data-testid={`growth-keyword-chip-${k.replace(/\s+/g, "-")}`}
              >
                {k}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-2 items-end">
            <div className="col-span-2">
              <label className="text-xs text-muted-foreground">Keyword</label>
              <Input value={kw} onChange={(e) => setKw(e.target.value)} placeholder="e.g. freight" className="h-9 mt-1" data-testid="growth-keyword-input" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Impressions</label>
              <Input type="number" min="0" value={impressions} onChange={(e) => setImpressions(e.target.value)} placeholder="0" className="h-9 mt-1" data-testid="growth-impressions-input" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Clicks</label>
              <Input type="number" min="0" value={clicks} onChange={(e) => setClicks(e.target.value)} placeholder="0" className="h-9 mt-1" data-testid="growth-clicks-input" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Avg position</label>
              <Input type="number" min="0" step="0.1" value={position} onChange={(e) => setPosition(e.target.value)} placeholder="optional" className="h-9 mt-1" data-testid="growth-position-input" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Date</label>
              <Input type="date" value={notedOn} onChange={(e) => setNotedOn(e.target.value)} className="h-9 mt-1" data-testid="growth-date-input" />
            </div>
          </div>
          <Button onClick={addEntry} disabled={saving} className="mt-3 bg-accent text-accent-foreground hover:bg-accent/90 h-9" data-testid="growth-add-entry-button">
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />} Log numbers
          </Button>

          <div className="mt-6">
            {seo === null ? <Skeleton className="h-24" /> : seo.length === 0 ? (
              <p className="text-sm text-muted-foreground" data-testid="growth-rank-empty">
                No entries yet. Open Search Console, check a keyword's impressions and clicks, and log the numbers above.
              </p>
            ) : (
              <Table data-testid="growth-rank-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Keyword</TableHead>
                    <TableHead className="text-right">Impressions</TableHead>
                    <TableHead className="text-right">Clicks</TableHead>
                    <TableHead className="text-right">Position</TableHead>
                    <TableHead className="text-right">Updated</TableHead>
                    <TableHead className="w-10"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {seo.map((k) => (
                    <TableRow key={k.keyword} data-testid={`growth-rank-row-${k.keyword.replace(/\s+/g, "-")}`}>
                      <TableCell className="text-sm font-medium">{k.keyword}</TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        {k.latest.impressions} <Delta latest={k.latest.impressions} previous={k.previous?.impressions} />
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        {k.latest.clicks} <Delta latest={k.latest.clicks} previous={k.previous?.clicks} />
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        {k.latest.position ?? "—"} {k.latest.position != null && <Delta latest={k.latest.position} previous={k.previous?.position} invert />}
                      </TableCell>
                      <TableCell className="text-right text-xs text-muted-foreground font-mono">{k.latest.noted_on}</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive"
                          onClick={() => deleteEntry(k.latest.id, k.keyword)}
                          aria-label={`Delete latest ${k.keyword} entry`}
                          data-testid={`growth-rank-delete-${k.keyword.replace(/\s+/g, "-")}`}>
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
