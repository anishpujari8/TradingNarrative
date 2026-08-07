import { useRef, useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Linkedin, Instagram, Link2, Share2, ImageDown, Download, Twitter } from "lucide-react";
import { toast } from "sonner";
import { SITE_URL, SITE_NAME, trackEvent } from "@/lib/api";

const wrapText = (ctx, text, maxWidth) => {
  const words = text.split(" ");
  const lines = [];
  let line = "";
  words.forEach((w) => {
    const test = line ? `${line} ${w}` : w;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = w;
    } else {
      line = test;
    }
  });
  if (line) lines.push(line);
  return lines;
};

const loadImage = (src) =>
  new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });

const drawCard = async (canvas, post, format, quoteText = "") => {
  const W = 1080;
  const H = format === "story" ? 1920 : 1080;
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d");

  // background
  ctx.fillStyle = "#101623";
  ctx.fillRect(0, 0, W, H);

  if (format === "quote") {
    const pad = 90;
    // giant quotation mark
    ctx.font = "700 220px 'EB Garamond', Georgia, serif";
    ctx.fillStyle = "#2ba08a";
    ctx.fillText("\u201C", pad - 20, 250);
    // quote text
    ctx.font = "500 58px 'EB Garamond', Georgia, serif";
    ctx.fillStyle = "#faf8f3";
    const qlines = wrapText(ctx, quoteText || post.excerpt || post.title, W - pad * 2);
    let qy = 360;
    qlines.slice(0, 8).forEach((l) => {
      ctx.fillText(l, pad, qy);
      qy += 76;
    });
    // attribution
    qy += 30;
    ctx.fillStyle = "#2ba08a";
    ctx.fillRect(pad, qy - 16, 44, 4);
    ctx.font = "400 34px 'Figtree', Arial, sans-serif";
    ctx.fillStyle = "rgba(250,248,243,0.75)";
    ctx.fillText(`${post.author?.name || "The Trading Narrative"} \u00B7 ${post.category_label || ""}`, pad + 60, qy);
    // footer brand
    const fy = H - 90;
    ctx.fillStyle = "#2ba08a";
    ctx.fillRect(pad, fy - 26, 16, 16);
    ctx.font = "600 40px 'EB Garamond', Georgia, serif";
    ctx.fillStyle = "#faf8f3";
    ctx.fillText(SITE_NAME, pad + 36, fy);
    return;
  }

  // cover image (top ~55%)
  const imgH = Math.round(H * 0.55);
  const img = await loadImage(post.cover_image);
  if (img) {
    const scale = Math.max(W / img.width, imgH / img.height);
    const dw = img.width * scale;
    const dh = img.height * scale;
    ctx.drawImage(img, (W - dw) / 2, (imgH - dh) / 2, dw, dh);
  } else {
    ctx.fillStyle = "#1d2739";
    ctx.fillRect(0, 0, W, imgH);
  }

  // gradient overlay from image into panel
  const grad = ctx.createLinearGradient(0, imgH - 300, 0, imgH + 10);
  grad.addColorStop(0, "rgba(16,22,35,0)");
  grad.addColorStop(1, "rgba(16,22,35,1)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, imgH - 300, W, 310);

  const pad = 80;
  let y = imgH + (format === "story" ? 120 : 70);

  // category label
  ctx.fillStyle = "#2ba08a";
  ctx.fillRect(pad, y - 14, 14, 14);
  ctx.font = "600 30px 'IBM Plex Mono', monospace";
  ctx.fillStyle = "rgba(250,248,243,0.75)";
  ctx.fillText((post.category_label || "").toUpperCase(), pad + 34, y);
  y += format === "story" ? 110 : 80;

  // title
  ctx.font = "600 76px 'EB Garamond', Georgia, serif";
  ctx.fillStyle = "#faf8f3";
  const lines = wrapText(ctx, post.title, W - pad * 2);
  lines.slice(0, 5).forEach((l) => {
    ctx.fillText(l, pad, y);
    y += 92;
  });

  y += format === "story" ? 60 : 30;
  // read time
  ctx.font = "400 32px 'Figtree', sans-serif";
  ctx.fillStyle = "rgba(250,248,243,0.6)";
  ctx.fillText(`${post.read_time} min read`, pad, y);

  // footer brand
  const fy = H - 90;
  ctx.fillStyle = "#2ba08a";
  ctx.fillRect(pad, fy - 26, 16, 16);
  ctx.font = "600 40px 'EB Garamond', Georgia, serif";
  ctx.fillStyle = "#faf8f3";
  ctx.fillText(SITE_NAME, pad + 36, fy);
};

const IgCardDialog = ({ post }) => {
  const canvasRef = useRef(null);
  const [format, setFormat] = useState("post");
  const [rendering, setRendering] = useState(false);
  const [quoteText, setQuoteText] = useState(post.excerpt || "");

  const render = async (fmt, qt) => {
    setRendering(true);
    if (canvasRef.current) await drawCard(canvasRef.current, post, fmt, qt !== undefined ? qt : quoteText);
    setRendering(false);
  };

  const download = () => {
    try {
      const url = canvasRef.current.toDataURL("image/png");
      const a = document.createElement("a");
      a.href = url;
      a.download = `${post.slug}-instagram-${format}.png`;
      a.click();
      toast.success("Image card downloaded — ready for Instagram.");
      trackEvent("ig_card_download", `/post/${post.slug}`, { format });
    } catch {
      toast.error("Could not export image (cover image blocked). Try again.");
    }
  };

  return (
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle className="font-serif text-2xl">Instagram share card</DialogTitle>
        <DialogDescription>
          Download a branded image sized for Instagram, then post it manually with the article
          link in your bio or story.
        </DialogDescription>
      </DialogHeader>
      <Tabs
        value={format}
        onValueChange={(v) => {
          setFormat(v);
          setTimeout(() => render(v), 50);
        }}
      >
        <TabsList className="grid grid-cols-3 w-full">
          <TabsTrigger value="post" data-testid="ig-card-format-post">Post</TabsTrigger>
          <TabsTrigger value="story" data-testid="ig-card-format-story">Story</TabsTrigger>
          <TabsTrigger value="quote" data-testid="ig-card-format-quote">Quote card</TabsTrigger>
        </TabsList>
        <TabsContent value="post" />
        <TabsContent value="story" />
        <TabsContent value="quote">
          <Textarea
            value={quoteText}
            onChange={(e) => setQuoteText(e.target.value)}
            onBlur={() => render("quote")}
            rows={3}
            maxLength={280}
            placeholder="Pick a line worth quoting\u2026"
            className="mt-2"
            data-testid="quote-card-text-input"
          />
          <p className="text-[10px] text-muted-foreground font-mono mt-1">Edit the quote, then click outside to refresh the preview.</p>
        </TabsContent>
      </Tabs>
      <div className="border border-border rounded-lg overflow-hidden bg-muted/40">
        <canvas
          ref={(el) => {
            canvasRef.current = el;
            if (el && !el.dataset.rendered) {
              el.dataset.rendered = "1";
              render(format);
            }
          }}
          className="w-full h-auto"
          data-testid="ig-card-canvas"
        />
      </div>
      <Button onClick={download} disabled={rendering} className="bg-accent text-accent-foreground hover:bg-accent/90 w-full" data-testid="share-download-ig-confirm">
        <Download className="h-4 w-4 mr-2" /> Download PNG
      </Button>
    </DialogContent>
  );
};

export const ShareBar = ({ post, orientation = "horizontal", idSuffix = "" }) => {
  // OG-rich share URL: crawlers read per-essay meta tags, humans get redirected to the article
  const unfurlUrl = `${SITE_URL}/api/share/${post.slug}`;

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(unfurlUrl);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = unfurlUrl;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    toast.success("Link copied — it unfurls with a rich preview card on LinkedIn and X.");
    trackEvent("share_copy_link", `/post/${post.slug}`);
  };

  const shareLinkedIn = () => {
    window.open(
      `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(unfurlUrl)}`,
      "_blank",
      "noopener,width=600,height=600"
    );
    trackEvent("share_linkedin", `/post/${post.slug}`);
  };

  const shareX = () => {
    window.open(
      `https://twitter.com/intent/tweet?url=${encodeURIComponent(unfurlUrl)}&text=${encodeURIComponent(post.title)}`,
      "_blank",
      "noopener,width=600,height=600"
    );
    trackEvent("share_x", `/post/${post.slug}`);
  };

  const webShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({ title: post.title, text: post.excerpt, url: unfurlUrl });
        trackEvent("share_native", `/post/${post.slug}`);
      } catch {
        /* user dismissed */
      }
    } else {
      copyLink();
    }
  };

  const btnCls = "border border-border rounded-lg hover:border-accent hover:text-accent transition-colors duration-150";
  const wrapCls =
    orientation === "vertical"
      ? "flex flex-col gap-2"
      : "flex flex-row flex-wrap gap-2";

  return (
    <TooltipProvider delayDuration={200}>
      <div className={wrapCls} data-testid={`share-bar${idSuffix}`}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className={btnCls} onClick={shareLinkedIn} data-testid={`share-linkedin-button${idSuffix}`} aria-label="Share on LinkedIn">
              <Linkedin className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">Share on LinkedIn</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className={btnCls} onClick={copyLink} data-testid={`share-copy-link-button${idSuffix}`} aria-label="Copy link for Instagram">
              <Instagram className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">Copy link for Instagram</TooltipContent>
        </Tooltip>

        <Dialog>
          <Tooltip>
            <TooltipTrigger asChild>
              <DialogTrigger asChild>
                <Button variant="ghost" size="icon" className={btnCls} data-testid={`share-download-ig-button${idSuffix}`} aria-label="Download Instagram card">
                  <ImageDown className="h-4 w-4" />
                </Button>
              </DialogTrigger>
            </TooltipTrigger>
            <TooltipContent side="right">Instagram image card</TooltipContent>
          </Tooltip>
          <IgCardDialog post={post} />
        </Dialog>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className={btnCls} onClick={shareX} data-testid={`share-x-button${idSuffix}`} aria-label="Share on X">
              <Twitter className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">Share on X</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className={btnCls} onClick={copyLink} data-testid={`share-plain-copy-button${idSuffix}`} aria-label="Copy link">
              <Link2 className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">Copy link</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className={btnCls} onClick={webShare} data-testid={`share-webshare-button${idSuffix}`} aria-label="Share">
              <Share2 className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">Share anywhere</TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
};
