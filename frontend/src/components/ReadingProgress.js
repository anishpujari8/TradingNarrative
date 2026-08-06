import { useEffect, useState } from "react";

export const ReadingProgress = ({ targetRef, readTime }) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const onScroll = () => {
      const el = targetRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const total = rect.height - window.innerHeight * 0.5;
      const scrolled = Math.min(Math.max(-rect.top + window.innerHeight * 0.25, 0), Math.max(total, 1));
      setProgress(total > 0 ? Math.min(scrolled / total, 1) : 1);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    onScroll();
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [targetRef]);

  const minutesLeft = Math.max(1, Math.ceil((readTime || 1) * (1 - progress)));
  const showPill = progress > 0.03 && progress < 0.97;

  return (
    <>
      <div className="fixed top-0 left-0 right-0 h-[3px] z-[70] pointer-events-none">
        <div
          className="h-full bg-accent transition-[width] duration-150 ease-out"
          style={{ width: `${progress * 100}%` }}
          data-testid="reading-progress-bar"
        />
      </div>
      <div
        className={`fixed bottom-5 right-5 z-40 bg-card border border-border rounded-full px-3.5 py-1.5 font-mono text-xs text-muted-foreground shadow-[var(--shadow-soft)] transition-opacity duration-300 ${showPill ? "opacity-100" : "opacity-0 pointer-events-none"}`}
        data-testid="reading-time-left"
      >
        ≈ {minutesLeft} min left
      </div>
    </>
  );
};
