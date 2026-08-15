import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { Seo } from "@/components/Seo";
import { CATEGORIES, SITE_URL, SITE_NAME } from "@/lib/api";
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
];

// Dedicated mascot showcase: the four pillars plus the two section identities.
export default function PillarsPage() {
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
              <div className="relative flex items-start gap-6">
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
                  <h2 className="font-serif text-2xl font-semibold mt-1">{lore?.name}</h2>
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

      <div className="mt-14" data-testid="pillars-sections">
        <span className="section-label">Also flying the flag</span>
        <h2 className="font-serif text-2xl sm:text-3xl font-semibold mt-3">Two more mascots on duty</h2>
        <div className="grid sm:grid-cols-2 gap-5 mt-6">
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
                  <h3 className="font-serif text-lg font-semibold mt-0.5">{lore?.name}</h3>
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
