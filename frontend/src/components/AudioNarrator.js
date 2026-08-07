import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Play, Pause, RotateCcw, Headphones, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";

const VOICES = [
  { key: "male", label: "George — warm male" },
  { key: "female", label: "Rachel — warm female" },
  { key: "documentary", label: "Daniel — documentary" },
];

const fmt = (s) => {
  if (!isFinite(s)) return "0:00";
  const m = Math.floor(s / 60);
  return `${m}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
};

export const AudioNarrator = ({ slug }) => {
  const [status, setStatus] = useState("idle"); // idle | loading | playing | paused | done
  const [voice, setVoice] = useState("male");
  const [rate, setRate] = useState("1");
  const [progress, setProgress] = useState({ t: 0, d: 0 });
  const audioRef = useRef(null);
  const urlsRef = useRef({}); // voice -> objectURL (per-essay cache in the browser)
  const listenedRef = useRef(false); // one listen counted per essay visit
  const milestonesRef = useRef(new Set()); // 25/50/75/100 — each reported once per visit

  // reset when navigating between essays
  useEffect(() => {
    setStatus("idle");
    setProgress({ t: 0, d: 0 });
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
      const detail = err?.response?.status === 502
        ? "Narration is temporarily unavailable. Try again shortly."
        : "Could not load the narration. Try again.";
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
            {status === "idle" && "Listen to this essay"}
            {status === "loading" && "Preparing narration — first play takes a moment…"}
            {status === "playing" && `${fmt(progress.t)} / ${fmt(progress.d)}`}
            {status === "paused" && `Paused — ${fmt(progress.t)} / ${fmt(progress.d)}`}
            {status === "done" && "Finished — play again?"}
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
    </div>
  );
};
