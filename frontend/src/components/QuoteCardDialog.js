import { useEffect, useRef, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Download, Copy, Share2 } from "lucide-react";
import { toast } from "sonner";

const CARD_W = 1200;
const CARD_H = 630;

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
  const accent = "#1c8570";

  // background + frame
  ctx.fillStyle = paper;
  ctx.fillRect(0, 0, CARD_W, CARD_H);
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
      toast.success("Copied — paste it anywhere");
    } catch {
      toast.error("Copying images isn't supported here — use Download instead.");
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
        toast("Link shared — use Download to attach the image itself.");
      } else {
        // desktop / in-app browsers: give them the image + guidance, never a dead end
        await download();
        toast("Image downloaded — attach it in WhatsApp, LinkedIn, or anywhere else.");
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
