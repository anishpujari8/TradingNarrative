import { Link } from "react-router-dom";
import { ArrowRight, BookOpen } from "lucide-react";
import { Seo } from "@/components/Seo";
import { SITE_URL, SITE_NAME } from "@/lib/api";
import { pillarAccent, withAlpha, PillarMotif } from "@/lib/pillars";

// Trading term glossary hub: every explainer essay collected on one crawlable page
// for topical authority. Each term answers the query in one breath, then links to
// the full essay. JSON-LD DefinedTermSet mirrors the on-page content.
const TERMS = [
  {
    term: "Demurrage",
    category: "finance",
    definition:
      "The penalty a charterer pays when loading or discharging a vessel runs past the agreed laytime, or when a container occupies the terminal beyond its free days.",
    slug: "what-is-demurrage-vs-detention-a-plain-english-guide-for-commodity-traders",
    essay: "What Is Demurrage vs Detention? A Plain-English Guide",
  },
  {
    term: "Detention",
    category: "finance",
    definition:
      "The charge for holding a carrier's equipment outside the terminal, typically a container that left the port but was not returned empty on time.",
    slug: "what-is-demurrage-vs-detention-a-plain-english-guide-for-commodity-traders",
    essay: "What Is Demurrage vs Detention? A Plain-English Guide",
  },
  {
    term: "Laytime",
    category: "finance",
    definition:
      "The period a charterparty grants to load or discharge cargo before demurrage begins to accrue. The clock that decides whether a voyage ends in a penalty or a despatch credit.",
    slug: "what-is-laytime-in-shipping-the-clock-that-decides-demurrage",
    essay: "What Is Laytime in Shipping? The Clock That Decides Demurrage",
  },
  {
    term: "TC/RC (Treatment & Refining Charges)",
    category: "finance",
    definition:
      "The fees a smelter charges a miner or trader for converting raw concentrate into refined metal, and a barometer for the balance of power between mines and smelters.",
    slug: "what-does-tc-rc-mean-in-metals-trading-treatment-and-refining-charges-explained",
    essay: "What Does TC/RC Mean in Metals Trading?",
  },
  {
    term: "ETRM (Energy Trading & Risk Management)",
    category: "tech-business",
    definition:
      "Software that manages the trading lifecycle for energy commodities: power, natural gas, oil, and increasingly carbon and renewables certificates.",
    slug: "etrm-vs-ctrm-whats-the-difference-and-which-one-do-you-actually-need",
    essay: "ETRM vs CTRM: What's the Difference?",
  },
  {
    term: "CTRM (Commodity Trading & Risk Management)",
    category: "tech-business",
    definition:
      "The broader category: everything ETRM does, extended across physical commodities like metals and agriculture, with deeper logistics, inventory, and quality functionality.",
    slug: "etrm-vs-ctrm-whats-the-difference-and-which-one-do-you-actually-need",
    essay: "ETRM vs CTRM: What's the Difference?",
  },
  {
    term: "Freight Visibility",
    category: "delivery",
    definition:
      "The ability to know, in real time, where cargo is, what condition it is in, and when it will actually arrive, not what a schedule claimed a week ago.",
    slug: "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr",
    essay: "Freight Management & Tracking Visibility",
  },
  {
    term: "Yield Curve Inversion",
    category: "finance",
    definition:
      "When short-term government bond yields rise above long-term yields, most commonly the 2-year Treasury paying more than the 10-year. A recession signal with direction, not timing.",
    slug: "reading-the-yield-curve-like-a-trader-not-a-tourist",
    essay: "Reading the Yield Curve Like a Trader, Not a Tourist",
  },
  {
    term: "Power Trading Desk",
    category: "delivery",
    definition:
      "A desk that buys and sells electricity across day-ahead, intraday, and balancing markets, managing generation, load, and grid constraints on hourly or faster clocks.",
    slug: "delivering-a-power-trading-desk-system-compliance-lifecycle-design-and-why-agile",
    essay: "Delivering a Power Trading Desk",
  },
];

export default function GlossaryPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "DefinedTermSet",
    name: `${SITE_NAME} Trading Glossary`,
    url: `${SITE_URL}/glossary`,
    hasDefinedTerm: TERMS.map((t) => ({
      "@type": "DefinedTerm",
      name: t.term,
      description: t.definition,
      url: `${SITE_URL}/post/${t.slug}`,
    })),
  };

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="glossary-page">
      <Seo
        title="Trading Glossary: Demurrage, Laytime, TC/RC, ETRM & More"
        description="Plain-English definitions of the commodity trading terms that decide P&L: demurrage, detention, laytime, TC/RC, ETRM vs CTRM, freight visibility, and more, each with a full explainer essay."
        path="/glossary"
        keywords="trading glossary, what is demurrage, laytime meaning, TC/RC metals, ETRM vs CTRM, freight visibility, commodity trading terms"
        jsonLd={jsonLd}
      />
      <span className="section-label">Glossary</span>
      <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3 max-w-3xl" data-testid="glossary-title">
        The trading terms that decide P&L, in plain English
      </h1>
      <p className="text-muted-foreground mt-5 max-w-2xl leading-relaxed">
        Every definition below answers the question in one breath, then links to a full essay
        with the mechanics, the failure modes, and what desks actually do about them. Written
        from twelve years of delivering trading systems, not from a textbook.
      </p>

      <div className="grid sm:grid-cols-2 gap-5 mt-10">
        {TERMS.map((t) => {
          const accent = pillarAccent(t.category);
          return (
            <Link
              key={t.term}
              to={`/post/${t.slug}`}
              className="group relative overflow-hidden bg-card border rounded-xl p-6 transition-[border-color,box-shadow] duration-200"
              style={{ borderColor: withAlpha(accent, 0.32) }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = withAlpha(accent, 0.7); }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = withAlpha(accent, 0.32); }}
              data-testid={`glossary-term-${t.term.split(" ")[0].toLowerCase().replace(/[^a-z]/g, "")}`}
            >
              <div className="absolute inset-y-0 right-0 w-1/2 pointer-events-none" style={{ color: accent, opacity: 0.08 }}>
                <PillarMotif category={t.category} className="h-full w-full" />
              </div>
              <dl className="relative">
                <dt className="font-serif text-xl font-semibold flex items-start gap-2.5">
                  <span className="mt-2 inline-block h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: accent }} aria-hidden />
                  {t.term}
                </dt>
                <dd className="text-sm text-muted-foreground mt-2.5 leading-relaxed">{t.definition}</dd>
              </dl>
              <span
                className="relative inline-flex items-center gap-1.5 text-sm font-medium mt-4 group-hover:gap-2.5 transition-all"
                style={{ color: accent }}
              >
                <BookOpen className="h-4 w-4" /> {t.essay} <ArrowRight className="h-4 w-4" />
              </span>
            </Link>
          );
        })}
      </div>

      <p className="text-sm text-muted-foreground mt-10">
        Want these explainers in your inbox as they publish?{" "}
        <Link to="/pricing" className="text-accent font-medium hover:underline" data-testid="glossary-pricing-link">
          Join the newsletter
        </Link>
        .
      </p>
    </div>
  );
}
