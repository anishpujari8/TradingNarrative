import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Play, Pause, RotateCcw, Headphones } from "lucide-react";

const cleanBlock = (b) => (b.startsWith("## ") ? b.slice(3) : b);

export const AudioNarrator = ({ title, blocks }) => {
  const [supported] = useState(() => typeof window !== "undefined" && "speechSynthesis" in window);
  const [status, setStatus] = useState("idle"); // idle | playing | paused | done
  const [index, setIndex] = useState(0);
  const [rate, setRate] = useState("1");
  const stateRef = useRef({ index: 0, rate: 1, stopped: true });

  const texts = [title, ...blocks.map(cleanBlock)].filter(Boolean);

  const speakFrom = (i) => {
    const synth = window.speechSynthesis;
    synth.cancel();
    stateRef.current.stopped = false;
    const speakNext = (j) => {
      if (stateRef.current.stopped) return;
      if (j >= texts.length) {
        setStatus("done");
        setIndex(0);
        stateRef.current.index = 0;
        return;
      }
      stateRef.current.index = j;
      setIndex(j);
      const u = new SpeechSynthesisUtterance(texts[j]);
      u.rate = stateRef.current.rate;
      u.lang = "en-US";
      u.onend = () => speakNext(j + 1);
      u.onerror = () => speakNext(j + 1);
      synth.speak(u);
    };
    setStatus("playing");
    speakNext(i);
  };

  const toggle = () => {
    const synth = window.speechSynthesis;
    if (status === "playing") {
      synth.pause();
      setStatus("paused");
    } else if (status === "paused") {
      synth.resume();
      setStatus("playing");
    } else {
      speakFrom(stateRef.current.index || 0);
    }
  };

  const restart = () => speakFrom(0);

  const changeRate = (v) => {
    setRate(v);
    stateRef.current.rate = parseFloat(v);
    if (status === "playing" || status === "paused") {
      speakFrom(stateRef.current.index); // re-speak the current paragraph at the new speed
    }
  };

  // stop narration when leaving the page
  useEffect(() => {
    return () => {
      stateRef.current.stopped = true;
      try { window.speechSynthesis.cancel(); } catch { /* ignore */ }
    };
  }, []);

  if (!supported || !texts.length) return null;

  const pct = status === "idle" ? 0 : Math.round((index / texts.length) * 100);

  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 mb-8" data-testid="audio-narrator">
      <Button
        size="icon"
        className="rounded-full bg-accent text-accent-foreground hover:bg-accent/90 shrink-0 h-10 w-10"
        onClick={toggle}
        aria-label={status === "playing" ? "Pause narration" : "Listen to this essay"}
        data-testid="audio-play-button"
      >
        {status === "playing" ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5" />}
      </Button>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 text-sm font-medium">
          <Headphones className="h-3.5 w-3.5 text-accent" />
          <span data-testid="audio-status-label">
            {status === "idle" && "Listen to this essay"}
            {status === "playing" && `Narrating — paragraph ${Math.max(1, index)} of ${texts.length - 1}`}
            {status === "paused" && "Paused"}
            {status === "done" && "Finished — play again?"}
          </span>
        </div>
        <div className="h-1 rounded-full bg-muted mt-2 overflow-hidden">
          <div className="h-full bg-accent transition-transform duration-300 origin-left" style={{ transform: `scaleX(${pct / 100})`, width: "100%" }} data-testid="audio-progress-bar" />
        </div>
      </div>

      {(status === "playing" || status === "paused") && (
        <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground hover:text-accent" onClick={restart} aria-label="Restart narration" data-testid="audio-restart-button">
          <RotateCcw className="h-4 w-4" />
        </Button>
      )}

      <Select value={rate} onValueChange={changeRate}>
        <SelectTrigger className="w-[76px] h-8 text-xs shrink-0" data-testid="audio-speed-select">
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
