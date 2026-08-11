import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Play, Pause, RotateCcw, Headphones, Loader2, Lock, Crown, CreditCard, IndianRupee } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const VOICES = [
  { key: "male", label: "George, warm male" },
  { key: "female", label: "Rachel, warm female" },
  { key: "documentary", label: "Daniel, documentary" },
];

const fmt = (s) => {
  if (!isFinite(s)) return "0:00";
  const m = Math.floor(s / 60);
  return `${m}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
};

const loadRazorpayScript = () =>
  new Promise((resolve, reject) => {
    if (window.Razorpay) return resolve();
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = resolve;
    script.onerror = reject;
    document.body.appendChild(script);
  });

export const AudioNarrator = ({ slug }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [status, setStatus] = useState("idle"); // idle | loading | playing | paused | done
  const [voice, setVoice] = useState("male");
  const [rate, setRate] = useState("1");
  const [scope, setScope] = useState(null); // 'full' | 'clip' (20s free preview)
  const [progress, setProgress] = useState({ t: 0, d: 0 });
  const [access, setAccess] = useState(null); // narration entitlement for this essay
  const [payOpen, setPayOpen] = useState(false);
  const [payBusy, setPayBusy] = useState(null); // 'razorpay' | 'stripe' | null
  const audioRef = useRef(null);
  const urlsRef = useRef({}); // voice -> objectURL (per-essay cache in the browser)
  const listenedRef = useRef(false); // one listen counted per essay visit
  const milestonesRef = useRef(new Set()); // 25/50/75/100, each reported once per visit
  const stripeHandledRef = useRef(false); // guard: process ?audio_session_id= once

  // reset when navigating between essays
  useEffect(() => {
    setStatus("idle");
    setProgress({ t: 0, d: 0 });
    setScope(null);
    listenedRef.current = false;
    milestonesRef.current = new Set();
    const urls = urlsRef.current;
    return () => {
      audioRef.current?.pause();
      audioRef.current = null;
      Object.values(urls).forEach((u) => URL.revokeObjectURL(u));
      urlsRef.current = {};
    };
  }, [slug]);

  // NARRATION ENTITLEMENT: premium = full; newsletter/shipping essays = free full audio;
  // everything else = 20s preview until a one-time ₹39 / $0.41 unlock
  const fetchAccess = useCallback(async () => {
    try {
      const res = await api.get(`/posts/${encodeURIComponent(slug)}/audio/access`);
      setAccess(res.data);
    } catch {
      setAccess(null);
    }
  }, [slug]);

  useEffect(() => { fetchAccess(); }, [fetchAccess, user?.id]);

  const clearAudioCache = () => {
    audioRef.current?.pause();
    audioRef.current = null;
    Object.values(urlsRef.current).forEach((u) => URL.revokeObjectURL(u));
    urlsRef.current = {};
    setStatus("idle");
    setScope(null);
    setProgress({ t: 0, d: 0 });
  };

  const celebrateUnlock = useCallback(() => {
    clearAudioCache();
    fetchAccess();
    toast.success("Full narration unlocked. It is yours forever, enjoy the listen.");
  }, [fetchAccess]);

  // Stripe return flow: /post/{slug}?audio_session_id=... -> poll until paid, then unlock
  useEffect(() => {
    const sid = searchParams.get("audio_session_id");
    if (!sid || stripeHandledRef.current) return;
    stripeHandledRef.current = true;
    let stopped = false;
    let attempts = 0;
    const clearParam = () => {
      const next = new URLSearchParams(searchParams);
      next.delete("audio_session_id");
      setSearchParams(next, { replace: true });
    };
    const poll = async () => {
      if (stopped) return;
      attempts += 1;
      try {
        const res = await api.get(`/payments/status/${sid}`);
        if (res.data.payment_status === "paid") {
          clearParam();
          celebrateUnlock();
          return;
        }
        if (res.data.status === "expired") {
          clearParam();
          toast.error("Payment session expired. No charge was made.");
          return;
        }
      } catch { /* transient, keep polling */ }
      if (attempts >= 8) {
        clearParam();
        toast.error("Payment confirmation is taking longer than expected. Refresh in a moment.");
        return;
      }
      setTimeout(poll, 2000);
    };
    poll();
    return () => { stopped = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const startUnlock = () => {
    if (!user) {
      // Purchase is saved to an account, so readers sign in first
      toast.info("Sign in first, your narration purchase is saved to your account.");
      navigate(`/auth?next=/post/${slug}`);
      return;
    }
    setPayOpen(true);
  };

  const payRazorpay = async () => {
    setPayBusy("razorpay");
    try {
      const res = await api.post("/billing/audio/razorpay/checkout", { slug });
      if (res.data.mock) {
        // MOCKED order — verify grants the unlock instantly
        await api.post("/billing/razorpay/verify", { order_id: res.data.order_id });
        setPayOpen(false);
        celebrateUnlock();
        return;
      }
      await loadRazorpayScript();
      const rzp = new window.Razorpay({
        key: res.data.razorpay_key_id,
        order_id: res.data.order_id,
        amount: res.data.amount,
        currency: res.data.currency,
        name: res.data.name,
        description: res.data.description,
        handler: async (resp) => {
          try {
            await api.post("/billing/razorpay/verify", {
              order_id: res.data.ref_id,
              payment_id: resp.razorpay_payment_id,
              signature: resp.razorpay_signature,
            });
            setPayOpen(false);
            celebrateUnlock();
          } catch {
            toast.error("Payment verification failed. Contact support.");
          }
        },
        modal: { ondismiss: () => setPayBusy(null) },
      });
      rzp.open();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not start Razorpay checkout.");
    } finally {
      setPayBusy(null);
    }
  };

  const payStripe = async () => {
    setPayBusy("stripe");
    try {
      const res = await api.post("/billing/audio/checkout", { slug, origin_url: window.location.origin });
      if (res.data.mock) {
        setPayOpen(false);
        celebrateUnlock();
        return;
      }
      window.location.href = res.data.checkout_url; // Stripe-hosted checkout
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not start checkout.");
      setPayBusy(null);
    }
  };

  const sendMilestone = (m) => {
    if (milestonesRef.current.has(m)) return;
    milestonesRef.current.add(m);
    api.post(`/posts/${encodeURIComponent(slug)}/audio/progress`, { milestone: m }).catch(() => {});
  };

  const attach = (audio) => {
    audio.playbackRate = parseFloat(rate);
    audio.ontimeupdate = () => {
      setProgress({ t: audio.currentTime, d: audio.duration || 0 });
      if (audio.duration) {
        const pct = (audio.currentTime / audio.duration) * 100;
        [25, 50, 75].forEach((m) => { if (pct >= m) sendMilestone(m); });
      }
    };
    audio.onended = () => {
      setStatus("done");
      sendMilestone(100);
    };
    audioRef.current = audio;
  };

  const ensureAudio = async (v) => {
    if (urlsRef.current[v]) return urlsRef.current[v];
    const res = await api.get(`/posts/${encodeURIComponent(slug)}/audio?voice=${v}`, {
      responseType: "blob",
      timeout: 180000, // first play synthesizes the narration
    });
    setScope(res.headers["x-audio-scope"] || "full");
    const url = URL.createObjectURL(res.data);
    urlsRef.current[v] = url;
    return url;
  };

  const trackListen = () => {
    if (listenedRef.current) return;
    listenedRef.current = true;
    api.post(`/posts/${encodeURIComponent(slug)}/audio/listen`).catch(() => {});
  };

  const play = async (v = voice) => {
    if (!user) {
      // NARRATION POLICY: sign-in required — free accounts get a 20-second preview
      toast.info("Sign in to listen, free accounts get a 20-second preview.", {
        action: { label: "Sign in", onClick: () => navigate(`/auth?next=/post/${slug}`) },
      });
      return;
    }
    try {
      if (audioRef.current && urlsRef.current[v] && audioRef.current.src === urlsRef.current[v]) {
        audioRef.current.play();
        setStatus("playing");
        trackListen();
        return;
      }
      setStatus("loading");
      const url = await ensureAudio(v);
      audioRef.current?.pause();
      const audio = new Audio(url);
      attach(audio);
      await audio.play();
      setStatus("playing");
      trackListen();
    } catch (err) {
      setStatus("idle");
      let detail = "Could not load the narration. Try again.";
      const data = err?.response?.data;
      if (data instanceof Blob) {
        try {
          const parsed = JSON.parse(await data.text());
          if (parsed?.detail) detail = parsed.detail;
        } catch { /* non-JSON error body, keep the default message */ }
      } else if (data?.detail) {
        detail = data.detail;
      } else if (err?.response?.status === 502) {
        detail = "Narration is temporarily unavailable. Try again shortly.";
      }
      toast.error(detail, { action: { label: "Retry", onClick: () => play(v) } });
    }
  };

  const toggle = () => {
    if (status === "playing") {
      audioRef.current?.pause();
      setStatus("paused");
    } else if (status === "paused") {
      audioRef.current?.play();
      setStatus("playing");
    } else if (status === "done") {
      if (audioRef.current) {
        audioRef.current.currentTime = 0;
        audioRef.current.play();
        setStatus("playing");
      } else {
        play();
      }
    } else if (status !== "loading") {
      play();
    }
  };

  const restart = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play();
      setStatus("playing");
    }
  };

  const changeVoice = (v) => {
    setVoice(v);
    const wasActive = status === "playing" || status === "paused" || status === "loading";
    audioRef.current?.pause();
    audioRef.current = null;
    setProgress({ t: 0, d: 0 });
    if (wasActive) {
      play(v);
    } else {
      setStatus("idle");
    }
  };

  const changeRate = (v) => {
    setRate(v);
    if (audioRef.current) audioRef.current.playbackRate = parseFloat(v);
  };

  const seek = (e) => {
    if (!audioRef.current || !progress.d) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const frac = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
    audioRef.current.currentTime = frac * progress.d;
  };

  const pct = progress.d ? Math.round((progress.t / progress.d) * 100) : 0;
  // gated = this reader would need the one-time unlock (or Premium) for the full track
  const gated = !!access?.unlockable && access?.enabled !== false;
  const freeAudio = !!access?.free_audio;
  const inr = Math.round(access?.price_inr ?? 45);
  const usd = (access?.price_usd ?? 0.5).toFixed(2);

  const idleLabel = () => {
    if (!user) return gated ? `Sign in to listen · unlock full audio for ₹${inr}` : "Sign in to listen to this essay";
    if (gated) return `20s free preview · unlock full audio for ₹${inr}`;
    if (freeAudio && !access?.is_premium) return "Listen to this essay · free narration";
    return "Listen to this essay";
  };

  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 mb-8" data-testid="audio-narrator">
      <Button
        size="icon"
        className="rounded-full bg-accent text-accent-foreground hover:bg-accent/90 shrink-0 h-10 w-10"
        onClick={toggle}
        disabled={status === "loading"}
        aria-label={status === "playing" ? "Pause narration" : "Listen to this essay"}
        data-testid="audio-play-button"
      >
        {status === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> :
          status === "playing" ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5" />}
      </Button>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 text-sm font-medium">
          <Headphones className="h-3.5 w-3.5 text-accent shrink-0" />
          <span className="truncate" data-testid="audio-status-label">
            {status === "idle" && idleLabel()}
            {status === "loading" && "Preparing narration, first play takes a moment…"}
            {status === "playing" && `${fmt(progress.t)} / ${fmt(progress.d)}${scope === "clip" ? " · free preview" : ""}`}
            {status === "paused" && `Paused, ${fmt(progress.t)} / ${fmt(progress.d)}`}
            {status === "done" && (scope === "clip" ? "Preview finished, unlock the full narration for ₹39" : "Finished, play again?")}
          </span>
        </div>
        <div
          className="h-1.5 rounded-full bg-muted mt-2 overflow-hidden cursor-pointer"
          onClick={seek}
          role="slider"
          aria-valuenow={pct}
          aria-label="Narration progress"
          data-testid="audio-progress-bar"
        >
          <div className="h-full bg-accent transition-transform duration-300 origin-left" style={{ transform: `scaleX(${pct / 100})`, width: "100%" }} />
        </div>
      </div>

      {gated && (
        <Button
          variant="outline"
          size="sm"
          className="shrink-0 h-8 text-xs border-accent/60 text-accent hover:bg-accent/10 hover:text-accent"
          onClick={startUnlock}
          data-testid="audio-unlock-button"
        >
          <Lock className="h-3 w-3 mr-1.5" /> Unlock · ₹{inr}
        </Button>
      )}

      {(status === "playing" || status === "paused") && (
        <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground hover:text-accent" onClick={restart} aria-label="Restart narration" data-testid="audio-restart-button">
          <RotateCcw className="h-4 w-4" />
        </Button>
      )}

      <Select value={voice} onValueChange={changeVoice}>
        <SelectTrigger className="w-[150px] h-8 text-xs shrink-0 hidden sm:flex" data-testid="audio-voice-select">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {VOICES.map((v) => <SelectItem key={v.key} value={v.key}>{v.label}</SelectItem>)}
        </SelectContent>
      </Select>

      <Select value={rate} onValueChange={changeRate}>
        <SelectTrigger className="w-[74px] h-8 text-xs shrink-0" data-testid="audio-speed-select">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="0.85">0.85×</SelectItem>
          <SelectItem value="1">1×</SelectItem>
          <SelectItem value="1.25">1.25×</SelectItem>
          <SelectItem value="1.5">1.5×</SelectItem>
        </SelectContent>
      </Select>

      {/* One-time narration unlock: pick Razorpay (INR) or Stripe (USD) */}
      <Dialog open={payOpen} onOpenChange={(o) => { if (!payBusy) setPayOpen(o); }}>
        <DialogContent className="sm:max-w-md" data-testid="audio-unlock-dialog">
          <DialogHeader>
            <DialogTitle className="font-serif text-2xl">Unlock this narration</DialogTitle>
            <DialogDescription>
              Own the full audio narration of this essay forever. One-time purchase, saved to your account.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <Button
              className="w-full justify-between bg-accent text-accent-foreground hover:bg-accent/90 h-11"
              onClick={payRazorpay}
              disabled={!!payBusy}
              data-testid="audio-pay-razorpay-button"
            >
              <span className="flex items-center"><IndianRupee className="h-4 w-4 mr-2" /> Pay ₹{inr} · UPI, cards, netbanking</span>
              {payBusy === "razorpay" ? <Loader2 className="h-4 w-4 animate-spin" /> : <span className="text-xs opacity-80">Razorpay</span>}
            </Button>
            <Button
              variant="outline"
              className="w-full justify-between h-11"
              onClick={payStripe}
              disabled={!!payBusy}
              data-testid="audio-pay-stripe-button"
            >
              <span className="flex items-center"><CreditCard className="h-4 w-4 mr-2" /> Pay ${usd} · international cards</span>
              {payBusy === "stripe" ? <Loader2 className="h-4 w-4 animate-spin" /> : <span className="text-xs opacity-70">Stripe</span>}
            </Button>
          </div>
          <DialogFooter className="sm:justify-start">
            <button
              className="text-xs text-muted-foreground hover:text-accent inline-flex items-center transition-colors"
              onClick={() => { setPayOpen(false); navigate("/pricing"); }}
              data-testid="audio-unlock-premium-link"
            >
              <Crown className="h-3 w-3 mr-1" /> Prefer everything? Go Premium, every essay and narration included
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
