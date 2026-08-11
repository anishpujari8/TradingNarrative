import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { UploadCloud, RefreshCw, Check, X } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";

/** Pushes the preview environment's cached narrations to the production site
 *  so live readers get instant audio without spending new ElevenLabs credits. */
export const SyncNarrationsDialog = ({ cachedCount = 0 }) => {
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [pushing, setPushing] = useState(false);
  const [results, setResults] = useState(null);

  const onOpenChange = (o) => {
    setOpen(o);
    if (o) {
      setPassword("");
      setResults(null);
    }
  };

  const push = () => {
    if (!password.trim()) {
      toast.error("Enter the production admin password first.");
      return;
    }
    setPushing(true);
    api.post("/admin/sync/narrations", { password })
      .then((res) => {
        setResults(res.data);
        if (res.data.pushed > 0) {
          toast.success(`Sent ${res.data.pushed} narration${res.data.pushed === 1 ? "" : "s"} to the live site.`);
        } else if (res.data.skipped > 0) {
          toast("Production already has every cached narration.");
        } else {
          toast("Nothing was pushed, see details in the dialog.");
        }
      })
      .catch((err) => toast.error(err?.response?.data?.detail || "Narration sync failed. Try again."))
      .finally(() => setPushing(false));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" disabled={cachedCount === 0} data-testid="admin-narrations-sync-button">
          <UploadCloud className="h-4 w-4 mr-2" /> Send narrations to live site
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg" data-testid="narration-sync-dialog">
        <DialogHeader>
          <DialogTitle className="font-serif text-2xl">Send narrations to production</DialogTitle>
          <DialogDescription>
            Copies the audio already generated here to your live site, so those essays play
            instantly for readers, no new ElevenLabs credits are used.
          </DialogDescription>
        </DialogHeader>

        {results ? (
          <div className="rounded-lg border border-border p-3 space-y-1.5 max-h-52 overflow-y-auto" data-testid="narration-sync-results">
            {results.results.length === 0 ? (
              <p className="text-sm text-muted-foreground">No matching essays on production yet, push the articles first via "Sync to production".</p>
            ) : (
              results.results.map((r) => (
                <div key={r.label} className="flex items-center gap-2 text-sm">
                  {r.ok ? <Check className="h-3.5 w-3.5 text-accent shrink-0" /> : <X className="h-3.5 w-3.5 text-destructive shrink-0" />}
                  <span className="flex-1 truncate font-mono text-xs">{r.label}</span>
                  {r.skipped && <span className="text-xs text-muted-foreground">already live</span>}
                  {!r.ok && <span className="text-xs text-destructive truncate max-w-[160px]">{r.detail}</span>}
                </div>
              ))
            )}
          </div>
        ) : (
          <div className="space-y-2">
            <Input
              type="password"
              placeholder="Production admin password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              data-testid="narration-sync-password-input"
            />
            <p className="text-[11px] text-muted-foreground">
              Used once to sign in to the live site's admin API, never stored.
            </p>
          </div>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setOpen(false)} data-testid="narration-sync-close-button">Close</Button>
          {!results && (
            <Button
              className="bg-accent text-accent-foreground hover:bg-accent/90"
              onClick={push}
              disabled={pushing}
              data-testid="narration-sync-push-button"
            >
              {pushing ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <UploadCloud className="h-4 w-4 mr-2" />}
              Send {cachedCount} narration{cachedCount === 1 ? "" : "s"}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
