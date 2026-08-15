import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, ScrollText } from "lucide-react";
import { Seo } from "@/components/Seo";
import { PostCard } from "@/components/PostCard";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { api, CATEGORIES, SITE_URL, SITE_NAME } from "@/lib/api";
import {
  pillarAccent,
  withAlpha,
  PillarMotif,
  pillarMascot,
  PILLAR_MASCOT_ALTS,
  PILLAR_TAGLINES,
  PILLAR_LORE,
} from "@/lib/pillars";

const SECTIONS = [
  { slug: "briefings", label: "The Weekly Briefing", to: "/briefings" },
  { slug: "books", label: "Bookshelf", to: "/books" },
  { slug: "lounge", label: "The Lounge", to: "/lounge" },
];

// Extended lore shown in the "Lore" tooltip on each mascot card.
const LORE_TOOLTIPS = {
  "tech-business":
    "The map of what's coming. How AI and emerging tech are rewiring trading systems, streamlining operations, and redrawing the competitive landscape — before most desks even realise it's happening.",
  finance:
    "Where commodities meet consequence. From crude to clean energy, the forces reshaping global trade — the markets, the money, and the transition that no desk can afford to ignore.",
  lifestyle:
    "The person behind the desk. Daily habits, hard lessons, and the quiet discipline that separates good traders from great ones — because markets test character before they test skill.",
  delivery:
    "The unglamorous engine room of every trade. From system implementation battles to the quiet wins of a workflow that finally works — this is where the real change happens.",
  briefings:
    "The wire never sleeps. Every Wednesday the falcon lands with five signals pulled from the noise of markets, tech, and trade — read them before the rest of the desk does.",
  books:
    "The long game. A shelf built slowly and honestly — books on trading, risk, and systems that survive contact with real markets, each one feeding back into the essays.",
  lounge:
    "The inner pack. A private room where Premium readers trade live takes, early drafts, and honest desk talk — because the best signal rarely comes from the crowd.",
};

// Small hoverable "Lore" chip; click never triggers the parent card link.
const LoreBadge = ({ slug, accent }) => (
  <TooltipProvider delayDuration={150}>
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          role="button"
          tabIndex={0}
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
          className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[9px] uppercase tracking-widest cursor-help transition-colors duration-150 shrink-0"
          style={{ color: accent, borderColor: withAlpha(accent, 0.45), backgroundColor: withAlpha(accent, 0.08) }}
          data-testid={`pillars-lore-badge-${slug}`}
          aria-label={`${slug} lore`}
        >
          <ScrollText className="h-3 w-3" /> Lore
        </span>
      </TooltipTrigger>
      <TooltipContent
        side="bottom"
        className="max-w-xs text-sm leading-relaxed"
        style={{ borderColor: withAlpha(accent, 0.5) }}
        data-testid={`pillars-lore-tooltip-${slug}`}
      >
        {LORE_TOOLTIPS[slug]}
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
);

// Dedicated mascot showcase: pillars + lore first, then the essays under each pillar.
export default function PillarsPage() {
  const [pillarPosts, setPillarPosts] = useState(null);

  useEffect(() => {
    let alive = true;
    Promise.all(
      CATEGORIES.map((c) =>
        api.get(`/posts?category=${c.slug}&limit=3`)
          .then((r) => [c.slug, r.data.posts || []])
          .catch(() => [c.slug, []])
      )
    ).then((pairs) => { if (alive) setPillarPosts(Object.fromEntries(pairs)); });
    return () => { alive = false; };
  }, []);

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: `The Pillars | ${SITE_NAME}`,
    url: `${SITE_URL}/pillars`,
    description:
      "The four pillars of The Trading Narrative: Tech & AI, Trading Business & Finance, Personal Growth, and Delivery & Systems, each with its own colour and mascot.",
    hasPart: CATEGORIES.map((c) => ({
      "@type": "WebPage",
      name: c.label,
      url: `${SITE_URL}/topics/${c.slug}`,
    })),
  };

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="pillars-page">
      <Seo
        title={`The Pillars | ${SITE_NAME}`}
        description="Four pillars, four colours, four mascots. Meet the Circuit Owl, the Sparkline Bull, the Rising Phoenix, and the Route Albatross, and explore what each pillar covers."
        path="/pillars"
        jsonLd={jsonLd}
      />

      <div className="max-w-2xl">
        <span className="section-label">The Pillars</span>
        <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3 leading-tight" data-testid="pillars-title">
          Four pillars, four colours, four mascots
        </h1>
        <p className="text-muted-foreground mt-5 leading-relaxed">
          Everything published here belongs to one of four pillars, and each pillar carries its own
          colour and emblem, on the site, on share cards, everywhere. Once you know the mascots,
          you can tell what an essay is about before you read a word.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mt-10">
        {CATEGORIES.map((c) => {
          const accent = pillarAccent(c.slug);
          const lore = PILLAR_LORE[c.slug];
          return (
            <Link
              key={c.slug}
              to={`/topics/${c.slug}`}
              className="group relative overflow-hidden bg-card border rounded-2xl p-7 sm:p-8 transition-[border-color,transform] duration-200 hover:-translate-y-0.5"
              style={{ borderColor: withAlpha(accent, 0.35), backgroundColor: withAlpha(accent, 0.05) }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = withAlpha(accent, 0.75); }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = withAlpha(accent, 0.35); }}
              data-testid={`pillars-card-${c.slug}`}
            >
              <div className="absolute inset-y-0 right-0 w-2/3 pointer-events-none" style={{ color: accent, opacity: 0.1 }}>
                <PillarMotif category={c.slug} className="h-full w-full" />
              </div>
              <div className="relative flex flex-col items-center text-center gap-5 sm:flex-row sm:items-start sm:text-left sm:gap-6">
                <img
                  src={pillarMascot(c.slug)}
                  alt={PILLAR_MASCOT_ALTS[c.slug]}
                  className="h-28 w-28 sm:h-32 sm:w-32 rounded-full object-cover shrink-0 shadow-lg"
                  style={{ border: `3px solid ${withAlpha(accent, 0.55)}` }}
                  loading="lazy"
                />
                <div className="min-w-0">
                  <span className="font-mono text-[10px] uppercase tracking-[0.16em]" style={{ color: accent }}>
                    {c.label}
                  </span>
                  <div className="flex items-center justify-center sm:justify-start gap-2 mt-1">
                    <h2 className="font-serif text-2xl font-semibold">{lore?.name}</h2>
                    <LoreBadge slug={c.slug} accent={accent} />
                  </div>
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{lore?.story}</p>
                  <p className="text-xs text-muted-foreground mt-2 italic">{PILLAR_TAGLINES[c.slug]}</p>
                  <span
                    className="inline-flex items-center gap-1 text-sm font-medium mt-3 group-hover:gap-2 transition-[gap] duration-150"
                    style={{ color: accent }}
                  >
                    Explore the pillar <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {pillarPosts && (
        <div className="mt-16" data-testid="pillars-essays">
          <span className="section-label">The essays</span>
          <h2 className="font-serif text-2xl sm:text-3xl font-semibold mt-3">Fresh from each pillar</h2>
          {CATEGORIES.map((c) => {
            const posts = pillarPosts[c.slug] || [];
            if (!posts.length) return null;
            const accent = pillarAccent(c.slug);
            return (
              <div key={c.slug} className="mt-10" data-testid={`pillars-essays-${c.slug}`}>
                <div className="flex items-center justify-between gap-4 mb-5">
                  <h3 className="font-serif text-xl font-semibold inline-flex items-center gap-2.5">
                    <span className="inline-block h-2.5 w-2.5 rounded-full shrink-0" style={{ backgroundColor: accent }} aria-hidden />
                    {c.label}
                  </h3>
                  <Link
                    to={`/topics/${c.slug}`}
                    className="text-sm font-medium inline-flex items-center gap-1 hover:gap-2 transition-[gap] duration-150 whitespace-nowrap"
                    style={{ color: accent }}
                    data-testid={`pillars-viewall-${c.slug}`}
                  >
                    View all <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {posts.map((p) => (
                    <PostCard key={p.slug} post={p} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-16" data-testid="pillars-sections">
        <span className="section-label">Also flying the flag</span>
        <h2 className="font-serif text-2xl sm:text-3xl font-semibold mt-3">Three more mascots on duty</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 mt-6">
          {SECTIONS.map((s) => {
            const accent = pillarAccent(s.slug);
            const lore = PILLAR_LORE[s.slug];
            return (
              <Link
                key={s.slug}
                to={s.to}
                className="group relative overflow-hidden bg-card border rounded-xl p-6 flex items-center gap-5 transition-[border-color] duration-200"
                style={{ borderColor: withAlpha(accent, 0.32) }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = withAlpha(accent, 0.7); }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = withAlpha(accent, 0.32); }}
                data-testid={`pillars-section-${s.slug}`}
              >
                <div className="absolute inset-y-0 right-0 w-1/2 pointer-events-none" style={{ color: accent, opacity: 0.08 }}>
                  <PillarMotif category={s.slug} className="h-full w-full" />
                </div>
                <img
                  src={pillarMascot(s.slug)}
                  alt={PILLAR_MASCOT_ALTS[s.slug]}
                  className="relative h-20 w-20 rounded-full object-cover shrink-0 shadow-md"
                  style={{ border: `3px solid ${withAlpha(accent, 0.55)}` }}
                  loading="lazy"
                />
                <div className="relative min-w-0">
                  <span className="font-mono text-[10px] uppercase tracking-[0.16em]" style={{ color: accent }}>
                    {s.label}
                  </span>
                  <div className="flex items-center gap-2 mt-0.5">
                    <h3 className="font-serif text-lg font-semibold">{lore?.name}</h3>
                    <LoreBadge slug={s.slug} accent={accent} />
                  </div>
                  <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{lore?.story}</p>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
