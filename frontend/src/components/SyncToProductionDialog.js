import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { UploadCloud, RefreshCw, Check, X, Globe } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";

export const SyncToProductionDialog = () => {
  const [open, setOpen] = useState(false);
  const [diff, setDiff] = useState(null);
  const [diffError, setDiffError] = useState(null);
  const [password, setPassword] = useState("");
  const [pushing, setPushing] = useState(false);
  const [results, setResults] = useState(null);

  const loadDiff = () => {
    setDiff(null);
    setDiffError(null);
    setResults(null);
    api.get("/admin/sync/diff")
      .then((res) => setDiff(res.data))
      .catch((err) => setDiffError(err?.response?.data?.detail || "Could not compare with production."));
  };

  const onOpenChange = (o) => {
    setOpen(o);
    if (o) {
      setPassword("");
      loadDiff();
    }
  };

  const push = () => {
    if (!password.trim()) {
      toast.error("Enter the production admin password first.");
      return;
    }
    setPushing(true);
    api.post("/admin/sync/push", { password })
      .then((res) => {
        setResults(res.data);
        const parts = [];
        if (res.data.pushed > 0) parts.push(`${res.data.pushed} new`);
        if (res.data.updated > 0) parts.push(`${res.data.updated} updated`);
        if (parts.length) {
          toast.success(`Synced to production: ${parts.join(", ")}.`);
        } else {
          toast(res.data.message || "Nothing to sync.");
        }
      })
      .catch((err) => toast.error(err?.response?.data?.detail || "Sync failed. Try again."))
      .finally(() => setPushing(false));
  };

  const host = diff?.production_url?.replace(/^https?:\/\//, "");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button variant="outline" data-testid="admin-sync-button">
          <UploadCloud className="h-4 w-4 mr-2" /> Sync to production
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg" data-testid="sync-dialog">
        <DialogHeader>
          <DialogTitle className="font-serif text-2xl">Sync to production</DialogTitle>
          <DialogDescription>
            Copies new published articles to your live site, and updates already-live articles whose details changed here (like a tier flipping to Premium).
          </DialogDescription>
        </DialogHeader>

        {diffError ? (
          <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm" data-testid="sync-diff-error">
            <p>{diffError}</p>
            <Button variant="outline" size="sm" className="mt-3" onClick={loadDiff} data-testid="sync-retry-button">
              <RefreshCw className="h-3.5 w-3.5 mr-2" /> Retry
            </Button>
          </div>
        ) : !diff ? (
          <div className="space-y-2" data-testid="sync-diff-loading">
            <Skeleton className="h-5 w-2/3" />
            <Skeleton className="h-16 rounded-lg" />
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2 text-sm text-muted-foreground" data-testid="sync-target">
              <Globe className="h-4 w-4 text-accent" />
              <span className="font-mono text-xs">{host}</span>
              <span>· {diff.production_published} published live</span>
            </div>

            {diff.missing.length === 0 && (!diff.outdated || diff.outdated.length === 0) ? (
              <div className="rounded-lg border border-border bg-muted/40 p-5 text-center" data-testid="sync-in-sync">
                <Check className="h-6 w-6 text-accent mx-auto mb-2" />
                <p className="text-sm">Production already matches preview. You're in sync.</p>
              </div>
            ) : (
              <>
                <div className="rounded-lg border border-border divide-y divide-border max-h-52 overflow-y-auto" data-testid="sync-missing-list">
                  {diff.missing.map((m) => (
                    <div key={m.slug} className="flex items-center gap-2 px-3 py-2.5 text-sm">
                      <Badge className="bg-accent/10 text-accent border-accent/30 hover:bg-accent/10 font-mono text-[10px] uppercase shrink-0">New</Badge>
                      <span className="flex-1 truncate">{m.title}</span>
                      {m.edition && <Badge variant="secondary" className="font-mono text-[10px]">Ed #{m.edition}</Badge>}
                      <Badge variant="outline" className="font-mono text-[10px] uppercase">{m.tier}</Badge>
                    </div>
                  ))}
                  {(diff.outdated || []).map((m) => (
                    <div key={m.slug} className="flex items-center gap-2 px-3 py-2.5 text-sm" data-testid={`sync-outdated-${m.slug}`}>
                      <Badge variant="secondary" className="font-mono text-[10px] uppercase shrink-0">Update</Badge>
                      <span className="flex-1 truncate">{m.title}</span>
                      <span className="text-[10px] text-muted-foreground font-mono truncate max-w-[130px]">{m.changed.join(", ")}</span>
                    </div>
                  ))}
                </div>

                {results ? (
                  <div className="rounded-lg border border-border p-3 space-y-1.5 max-h-40 overflow-y-auto" data-testid="sync-results">
                    {results.results.map((r) => (
                      <div key={`${r.action}-${r.slug}`} className="flex items-center gap-2 text-sm">
                        {r.ok ? <Check className="h-3.5 w-3.5 text-accent shrink-0" /> : <X className="h-3.5 w-3.5 text-destructive shrink-0" />}
                        <span className="flex-1 truncate">{r.title}</span>
                        <span className="text-[10px] text-muted-foreground font-mono uppercase">{r.action}</span>
                        {!r.ok && <span className="text-xs text-destructive truncate max-w-[140px]">{r.detail}</span>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Input
                      type="password"
                      placeholder="Production admin password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      data-testid="sync-password-input"
                    />
                    <p className="text-[11px] text-muted-foreground">
                      Used once to sign in to the live site's admin API — never stored.
                    </p>
                  </div>
                )}

                <div className="flex justify-end gap-2">
                  <Button variant="ghost" onClick={() => setOpen(false)} data-testid="sync-close-button">Close</Button>
                  {!results && (
                    <Button
                      className="bg-accent text-accent-foreground hover:bg-accent/90"
                      onClick={push}
                      disabled={pushing}
                      data-testid="sync-push-button"
                    >
                      {pushing ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <UploadCloud className="h-4 w-4 mr-2" />}
                      Sync {diff.missing.length + (diff.outdated?.length || 0)} article{diff.missing.length + (diff.outdated?.length || 0) === 1 ? "" : "s"}
                    </Button>
                  )}
                </div>
              </>
            )}
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};
