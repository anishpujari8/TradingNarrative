import { Link } from "react-router-dom";
import { SITE_URL } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Seo } from "@/components/Seo";
import { Linkedin, Instagram, ArrowRight } from "lucide-react";
import { NewsletterForm } from "@/components/NewsletterForm";
import { FoundingWall } from "@/components/FoundingWall";
import { CATEGORIES } from "@/lib/api";
import { pillarAccent, withAlpha, pillarMascot, PILLAR_MASCOT_ALTS, PILLAR_TAGLINES, PillarMotif } from "@/lib/pillars";

// Mascot lore: how each pillar's emblem maps to what the essays actually cover.
const MASCOT_LORE = {
  "tech-business": {
    name: "The Circuit Owl",
    story: "Sees in the dark and reads the wiring underneath. Essays on ETRM, CTRM, and what AI actually changes on a trading desk.",
  },
  finance: {
    name: "The Sparkline Bull",
    story: "Built from the chart itself. Market mechanics from yield curves to treatment charges, explained like a desk would.",
  },
  lifestyle: {
    name: "The Rising Phoenix",
    story: "Every cycle ends in a better start. Life systems for operators: deep work, habits, and deliberate resets.",
  },
  delivery: {
    name: "The Route Albatross",
    story: "Flies the whole route and lands where it planned. How complex trading platforms actually get shipped and adopted.",
  },
};

export default function AboutPage() {
  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="about-page">
      <Seo
        title="About"
        description="The story behind The Trading Narrative and its author, Anish Pujari."
        path="/about"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "AboutPage",
          name: "About The Trading Narrative",
          url: `${SITE_URL}/about`,
          mainEntity: {
            "@type": "Person",
            name: "Anish Pujari",
            jobTitle: "Founder & Author",
            worksFor: { "@type": "Organization", name: "The Trading Narrative", url: SITE_URL },
            knowsAbout: ["commodity trading", "energy markets", "trading technology", "ETRM", "market risk", "freight and shipping"],
          },
        }}
      />
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 items-start">
        <div className="lg:col-span-5">
          <div className="rounded-2xl overflow-hidden border border-border shadow-[var(--shadow-float)] card-img-zoom">
            <img
              src="/anish.jpg"
              alt="Anish Pujari, author of The Trading Narrative"
              className="w-full aspect-[4/5] object-cover"
              data-testid="about-author-photo"
            />
          </div>
        </div>
        <div className="lg:col-span-7">
          <span className="section-label">About</span>
          <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3 leading-tight">
            Markets tell stories. I write them down.
          </h1>
          <div className="article-body mt-8">
            <p>
              I'm Anish Pujari, a senior product and engagement manager who's spent over 12 years
              inside commodity trading floors, watching multi-million-pound technology programmes
              succeed or collapse for reasons that had nothing to do with the technology. This
              publication is my answer to that gap.
            </p>
            <p>
              It covers four things I've built a career around: technology and AI reshaping
              enterprise systems and how work actually gets delivered, the business and financial
              mechanics behind high-stakes client engagements, budgets, negotiation, governance,
              without the jargon, the unglamorous systems that let large programmes run on time
              and under budget instead of quietly falling apart, and the personal growth that
              comes from managing complexity, stakeholders, teams, ambiguity, rather than just
              headcount.
            </p>
            <p>
              Every piece follows the same rule: it must be something I'd tell a colleague who's
              about to walk into a steering committee and needs the real answer, not the safe one.
              No buzzwords, no theory without a delivery scar to back it up.
            </p>
            <p>
              Free subscribers get a full essay every week and previews of premium work. Premium
              members get the full library, ad-free reading, and early access before anything
              goes public.
            </p>
          </div>
          <Separator className="my-8" />
          <div className="bg-muted/40 border border-border rounded-2xl p-6">
            <h3 className="font-serif text-xl font-semibold mb-1">Join the readers</h3>
            <p className="text-sm text-muted-foreground mb-4">Get the next narrative in your inbox.</p>
            <NewsletterForm source="about" testId="about-newsletter-form" />
            <div className="mt-4 flex flex-wrap gap-3">
              <Link to="/pricing">
                <Button variant="outline" className="w-full sm:w-auto" data-testid="about-pricing-button">Explore Premium</Button>
              </Link>
              <a href="https://www.linkedin.com/in/anish-pujari-69174b6a" target="_blank" rel="noopener noreferrer">
                <Button variant="outline" className="gap-2" data-testid="about-linkedin-button"><Linkedin className="h-4 w-4" /> Follow on LinkedIn</Button>
              </a>
              <a href="https://www.instagram.com/anishpujari8" target="_blank" rel="noopener noreferrer">
                <Button variant="outline" className="gap-2" data-testid="about-instagram-button"><Instagram className="h-4 w-4" /> Follow on Instagram</Button>
              </a>
            </div>
          </div>
        </div>
      </div>

      <Separator className="my-14" />

      <section data-testid="about-book-section">
        <span className="section-label">The Book</span>
        <div className="grid md:grid-cols-12 gap-8 md:gap-12 items-center mt-6">
          <div className="md:col-span-4">
            <img
              src="/book-cover.webp"
              alt="How Trading Can Make You Money by Anish Pujari, book cover"
              className="rounded-2xl border border-border shadow-[var(--shadow-float)] w-full max-w-sm mx-auto"
              loading="lazy"
              data-testid="about-book-cover"
            />
          </div>
          <div className="md:col-span-8">
            <h2 className="font-serif text-3xl sm:text-4xl font-semibold">
              How Trading Can Make You Money
            </h2>
            <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground mt-2">
              An Honest Beginner's Roadmap: Strategies, AI Prompts & a 12-Month Plan
            </p>
            <p className="text-muted-foreground mt-5 leading-relaxed max-w-2xl">
              Trading can generate real income, but roughly 90% of retail traders lose money,
              SEBI's own F&O data says so. Not because trading doesn't work, but because they
              skip risk management, trade too big, and have no process. The book's promise:
              teach the habits of the profitable 10% from day one.
            </p>
            <div className="flex items-center gap-4 mt-6 flex-wrap">
              <a
                href="https://www.amazon.in/dp/B0HBR9THSX"
                target="_blank"
                rel="noopener noreferrer"
                data-testid="about-book-buy-link"
              >
                <Button className="gap-2 bg-accent text-accent-foreground hover:bg-accent/90">
                  Get the book <ArrowRight className="h-4 w-4" />
                </Button>
              </a>
              <a
                href="https://www.linkedin.com/build-relation/newsletter-follow?entityUrn=7490310794455306241"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-accent font-medium hover:underline"
                data-testid="about-book-linkedin-newsletter-link"
              >
                Subscribe on LinkedIn →
              </a>
            </div>
          </div>
        </div>
      </section>

      <Separator className="my-14" />

      <section data-testid="about-pillars-section">
        <span className="section-label">The Pillars</span>
        <h2 className="font-serif text-3xl sm:text-4xl font-semibold mt-3">
          Four pillars, four colours, four mascots
        </h2>
        <p className="text-muted-foreground mt-4 max-w-2xl leading-relaxed">
          Everything published here belongs to one of four pillars, and each pillar carries its
          own colour and emblem, on the site, on share cards, everywhere. Once you know the
          mascots, you can tell what an essay is about before you read a word.
        </p>
        <div className="grid sm:grid-cols-2 gap-5 mt-8">
          {CATEGORIES.map((c) => {
            const accent = pillarAccent(c.slug);
            const lore = MASCOT_LORE[c.slug];
            return (
              <Link
                key={c.slug}
                to={`/topics/${c.slug}`}
                className="group relative overflow-hidden bg-card border rounded-xl p-6 flex items-center gap-5 transition-[border-color] duration-200"
                style={{ borderColor: withAlpha(accent, 0.32) }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = withAlpha(accent, 0.7); }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = withAlpha(accent, 0.32); }}
                data-testid={`about-pillar-${c.slug}`}
              >
                <div className="absolute inset-y-0 right-0 w-1/2 pointer-events-none" style={{ color: accent, opacity: 0.07 }}>
                  <PillarMotif category={c.slug} className="h-full w-full" />
                </div>
                <img
                  src={pillarMascot(c.slug)}
                  alt={PILLAR_MASCOT_ALTS[c.slug]}
                  className="relative h-24 w-24 rounded-full object-cover shrink-0 shadow-md"
                  style={{ border: `3px solid ${withAlpha(accent, 0.55)}` }}
                  loading="lazy"
                />
                <div className="relative min-w-0">
                  <span className="font-mono text-[10px] uppercase tracking-[0.16em]" style={{ color: accent }}>
                    {c.label}
                  </span>
                  <h3 className="font-serif text-xl font-semibold mt-0.5">{lore?.name}</h3>
                  <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">{lore?.story}</p>
                  <span className="inline-flex items-center gap-1 text-sm font-medium mt-2 group-hover:gap-2 transition-all" style={{ color: accent }}>
                    Explore the pillar <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      <FoundingWall />
    </div>
  );
}
