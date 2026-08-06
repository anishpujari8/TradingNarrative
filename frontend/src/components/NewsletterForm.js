import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Loader2, MailCheck } from "lucide-react";
import { api, trackEvent } from "@/lib/api";

export const NewsletterForm = ({ source = "site", compact = false, testId = "newsletter-inline-form" }) => {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!email || !email.includes("@")) {
      toast.error("Please enter a valid email address.");
      return;
    }
    setBusy(true);
    try {
      const res = await api.post("/newsletter/subscribe", { email, source });
      setDone(true);
      toast.success(res.data.message);
      trackEvent("newsletter_subscribe_ui", source);
      setEmail("");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Something went wrong. Try again.");
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <div
        className="flex items-center gap-2 text-sm text-accent font-medium py-2"
        data-testid="newsletter-success-message"
      >
        <MailCheck className="h-4 w-4" /> You're on the list. Welcome aboard.
      </div>
    );
  }

  return (
    <form onSubmit={submit} className={`flex ${compact ? "flex-row" : "flex-col sm:flex-row"} gap-2 w-full`} data-testid={testId}>
      <Input
        type="email"
        placeholder="you@example.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="bg-card h-11"
        data-testid="newsletter-email-input"
      />
      <Button
        type="submit"
        disabled={busy}
        className="h-11 bg-accent text-accent-foreground hover:bg-accent/90 px-6 shrink-0"
        data-testid="newsletter-submit-button"
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Subscribe"}
      </Button>
    </form>
  );
};
