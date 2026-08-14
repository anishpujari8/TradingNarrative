import { useEffect, useRef, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Download, Copy, Share2 } from "lucide-react";
import { toast } from "sonner";

const CARD_W = 1200;
const CARD_H = 630;

// Pillar accents + signature motifs, mirroring the backend OG share cards
// (services/og_service.py) so every shared artifact carries the pillar identity.
const PILLAR_ACCENTS = {
  "tech-business": "#7a73e8", // violet — Tech & AI
  finance: "#1c8570", // brand teal — Business & Finance
  lifestyle: "#c4872e", // warm amber — Personal Growth
  delivery: "#3f7cc4", // steel blue — Delivery & Systems
};

const bezier = (p0, p1, p2, n = 120) => {
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    pts.push([
      (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
      (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1],
    ]);
  }
  return pts;
};

// Each motif is drawn in the pillar accent at low opacity so the quote stays king.
const drawMotif = (ctx, category, accent) => {
  ctx.save();
  ctx.strokeStyle = accent;
  ctx.fillStyle = accent;
  ctx.lineWidth = 2;
  if (category === "finance") {
    // ascending sparkline along the lower canvas
    const pts = [[70, 588], [200, 548], [330, 566], [460, 500], [590, 524], [720, 456], [850, 478], [980, 404], [1130, 430]];
    ctx.globalAlpha = 0.16;
    ctx.beginPath();
    pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    ctx.stroke();
    ctx.globalAlpha = 0.22;
    pts.forEach(([x, y]) => { ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.fill(); });
  } else if (category === "tech-business") {
    // circuit traces with solder pads (top-right + bottom-left)
    const traces = [
      [[880, 84], [1030, 84], [1064, 118], [1064, 240]],
      [[1128, 300], [1128, 430], [1094, 464], [960, 464]],
      [[70, 566], [300, 566], [334, 532], [520, 532]],
    ];
    ctx.globalAlpha = 0.18;
    for (const tr of traces) {
      ctx.beginPath();
      tr.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
      ctx.stroke();
      const [sx, sy] = tr[0];
      const [ex, ey] = tr[tr.length - 1];
      for (const [x, y] of [[sx, sy], [ex, ey]]) {
        ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI * 2); ctx.stroke();
        ctx.beginPath(); ctx.arc(x, y, 1.8, 0, Math.PI * 2); ctx.fill();
      }
    }
  } else if (category === "lifestyle") {
    // sunrise arcs radiating from the top-right corner
    ctx.globalAlpha = 0.15;
    for (let r = 90; r <= 420; r += 66) {
      ctx.beginPath();
      ctx.arc(1180, -40, r, Math.PI * 0.48, Math.PI * 1.02);
      ctx.stroke();
    }
    ctx.globalAlpha = 0.3;
    for (const [x, y] of [[1000, 300], [1090, 386], [906, 224]]) {
      ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.fill();
    }
  } else if (category === "delivery") {
    // dashed route with ringed waypoints and destination
    const path = bezier([80, 580], [620, 660], [1130, 140], 140);
    ctx.globalAlpha = 0.2;
    ctx.setLineDash([14, 12]);
    ctx.beginPath();
    path.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 0.28;
    for (const t of [0, 0.35, 0.7]) {
      const [x, y] = path[Math.round(t * (path.length - 1))];
      ctx.beginPath(); ctx.arc(x, y, 6, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.arc(x, y, 1.8, 0, Math.PI * 2); ctx.fill();
    }
    const [dx, dy] = path[path.length - 1];
    ctx.beginPath(); ctx.arc(dx, dy, 10, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.arc(dx, dy, 3, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
};

const wrapText = (ctx, text, maxWidth) => {
  const words = text.split(" ");
  const lines = [];
  let line = "";
  for (const w of words) {
    const test = line ? `${line} ${w}` : w;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = w;
    } else {
      line = test;
    }
  }
  if (line) lines.push(line);
  return lines;
};

const drawCard = (canvas, highlight) => {
  const ctx = canvas.getContext("2d");
  const scale = 2; // retina-crisp export
  canvas.width = CARD_W * scale;
  canvas.height = CARD_H * scale;
  ctx.scale(scale, scale);

  const paper = "#f7f5f0";
  const ink = "#14181f";
  const muted = "#6b7280";
  const accent = PILLAR_ACCENTS[highlight.category] || "#1c8570";

  // background + frame
  ctx.fillStyle = paper;
  ctx.fillRect(0, 0, CARD_W, CARD_H);
  drawMotif(ctx, highlight.category, accent);
  ctx.strokeStyle = "rgba(20,24,31,0.12)";
  ctx.lineWidth = 2;
  ctx.strokeRect(28, 28, CARD_W - 56, CARD_H - 56);

  // masthead
  ctx.fillStyle = accent;
  ctx.fillRect(72, 84, 14, 14);
  ctx.fillStyle = ink;
  ctx.font = "600 20px 'Courier New', monospace";
  ctx.fillText("T H E   T R A D I N G   N A R R A T I V E", 104, 98);

  // decorative quote mark
  ctx.fillStyle = accent;
  ctx.font = "italic 700 130px Georgia, serif";
  ctx.fillText("\u201C", 62, 220);

  // quote text — size adapts to length
  const t = highlight.text;
  const size = t.length <= 120 ? 52 : t.length <= 240 ? 42 : t.length <= 380 ? 34 : 28;
  ctx.fillStyle = ink;
  ctx.font = `500 ${size}px 'EB Garamond', Georgia, serif`;
  const lines = wrapText(ctx, `${t}\u201D`, CARD_W - 300);
  const lineH = size * 1.35;
  const blockH = lines.length * lineH;
  let y = Math.max(238, 214 + (300 - blockH) / 2);
  for (const line of lines) {
    ctx.fillText(line, 150, y);
    y += lineH;
  }

  // footer: essay title + author, accent bar
  ctx.fillStyle = accent;
  ctx.fillRect(72, CARD_H - 130, 46, 4);
  ctx.fillStyle = ink;
  ctx.font = "italic 600 24px Georgia, serif";
  const title = highlight.post_title.length > 72 ? `${highlight.post_title.slice(0, 70)}\u2026` : highlight.post_title;
  ctx.fillText(title, 72, CARD_H - 96);
  ctx.fillStyle = muted;
  ctx.font = "400 18px 'Courier New', monospace";
  ctx.fillText(`\u2014 Anish Pujari \u00B7 ${highlight.category_label}`, 72, CARD_H - 64);
};

export const QuoteCardDialog = ({ highlight, open, onOpenChange }) => {
  const canvasRef = useRef(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open || !highlight) return;
    // let fonts settle before drawing
    const draw = () => canvasRef.current && drawCard(canvasRef.current, highlight);
    if (document.fonts?.ready) {
      document.fonts.ready.then(() => setTimeout(draw, 50));
    } else {
      setTimeout(draw, 100);
    }
  }, [open, highlight]);

  const toBlob = () =>
    new Promise((resolve, reject) => {
      canvasRef.current.toBlob((b) => (b ? resolve(b) : reject(new Error("render failed"))), "image/png");
    });

  const download = async () => {
    try {
      const a = document.createElement("a");
      a.href = canvasRef.current.toDataURL("image/png");
      a.download = "trading-narrative-quote.png";
      a.click();
      toast.success("Quote card downloaded");
    } catch {
      toast.error("Could not create the image. Try again.");
    }
  };

  const copyImage = async () => {
    setBusy(true);
    try {
      const blob = await toBlob();
      await navigator.clipboard.write([new window.ClipboardItem({ "image/png": blob })]);
      toast.success("Copied, paste it anywhere");
    } catch {
      toast.error("Copying images isn't supported here, use Download instead.");
    } finally {
      setBusy(false);
    }
  };

  const share = async () => {
    setBusy(true);
    try {
      const blob = await toBlob();
      const file = new File([blob], "trading-narrative-quote.png", { type: "image/png" });
      if (navigator.canShare?.({ files: [file] })) {
        // native sheet with the image attached (iOS Safari, Android Chrome)
        await navigator.share({ files: [file], title: "The Trading Narrative" });
      } else if (navigator.share) {
        // device can share text/links but not files — share the essay link instead
        await navigator.share({ title: "The Trading Narrative", url: window.location.href });
        toast("Link shared, use Download to attach the image itself.");
      } else {
        // desktop / in-app browsers: give them the image + guidance, never a dead end
        await download();
        toast("Image downloaded, attach it in WhatsApp, LinkedIn, or anywhere else.");
      }
    } catch (e) {
      if (e?.name !== "AbortError") {
        await download();
        toast("Sharing isn't supported here, so the image was downloaded instead.");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl" data-testid="quote-card-dialog">
        <DialogHeader>
          <DialogTitle className="font-serif text-2xl">Share this line</DialogTitle>
          <DialogDescription>A quote card ready for LinkedIn, X, or anywhere else.</DialogDescription>
        </DialogHeader>
        <div className="rounded-xl overflow-hidden border border-border shadow-sm">
          <canvas
            ref={canvasRef}
            style={{ width: "100%", height: "auto", display: "block" }}
            data-testid="quote-card-canvas"
          />
        </div>
        <div className="flex flex-col sm:flex-row gap-2 justify-end">
          <Button variant="outline" onClick={copyImage} disabled={busy} data-testid="quote-card-copy-button">
            <Copy className="h-4 w-4 mr-2" /> Copy image
          </Button>
          <Button variant="outline" onClick={share} disabled={busy} data-testid="quote-card-share-button">
            <Share2 className="h-4 w-4 mr-2" /> Share
          </Button>
          <Button className="bg-accent text-accent-foreground hover:bg-accent/90" onClick={download} data-testid="quote-card-download-button">
            <Download className="h-4 w-4 mr-2" /> Download PNG
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
