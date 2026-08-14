import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { ArrowRight } from "lucide-react";
import { Seo } from "@/components/Seo";
import { PostCard } from "@/components/PostCard";
import { api, CATEGORIES, SITE_URL } from "@/lib/api";
import { pillarAccent, withAlpha, PillarMotif, pillarMascot, PILLAR_MASCOT_ALTS } from "@/lib/pillars";

// Topic hubs: original intro copy (200-400 words) per pillar. These pages are the
// SEO landing surfaces for head terms; each hub links every essay under the theme
// and back to the full archive. Keep intros original — never paste essay text here.
const TOPIC_INTROS = {
  "tech-business": {
    title: "Technology & AI on the Trading Desk",
    paragraphs: [
      "Commodity and energy trading runs on systems most people never see: ETRM and CTRM platforms that price physical deals, risk engines that re-run books overnight, scheduling tools that move real molecules and megawatts, and now a wave of AI agents promising to automate the middle office. This hub collects every Trading Narrative essay on that stack, written from inside the implementations rather than from a vendor's slide deck.",
      "The through-line in these essays is a simple belief: technology choices on a trading desk are business choices. A CTRM that cannot represent negative treatment charges will misprice a concentrates book. A batch-based end-of-day process becomes a liability the day regulators approve 24/7 futures. An AI copilot is only as good as the deal data underneath it. We look at what actually breaks, what actually ships, and what desks should demand from their vendors before signing.",
      "Expect deep dives on ETRM/CTRM selection and delivery, agentic AI in commodity workflows, market data infrastructure, surveillance and compliance tech, and the occasional teardown of why a promising platform died in distribution. If you work on or around a trading desk, in product, IT, risk, or the front office itself, these essays are written for you.",
    ],
  },
  finance: {
    title: "Trading, Business & Finance, from Markets to Mechanics",
    paragraphs: [
      "Markets are stories the money tells itself, and this hub is where The Trading Narrative reads them out loud. It gathers our essays on business and financial mechanics: how commodity prices actually move, how desks position around OPEC+ decisions and USDA reports, how freight rates and yield curves leak information about the real economy, and how the shipping industry quietly sits on billion-dollar inefficiencies.",
      "These essays favour mechanism over prediction. Instead of calling the next move in Brent, we unpack what a negative treatment charge means for smelter margins, why a 5% single-day slide in crude is really a stress test for intraday VaR, and what the first survey-based corn yield of the season does to grain volatility. The aim is that after each essay you understand one more gear in the machine, whether you run a book, build the systems behind one, or simply want to read markets with sharper eyes.",
      "Trading, Business & Finance essays are the free backbone of the publication, and the weekly briefings live here too. Start with the latest edition, then work back through the archive.",
    ],
  },
  delivery: {
    title: "Delivery & Systems: How Big Programmes Actually Ship",
    paragraphs: [
      "Every trading firm has a graveyard of stalled system implementations, and almost none of them died for technical reasons. This hub collects The Trading Narrative's essays on delivery: the unglamorous discipline of getting a complex platform, an ETRM replacement, a power desk build-out, a compliance stack, from contract signature to a desk that actually uses it.",
      "The essays draw on years spent as a product manager inside these programmes. They cover the mechanics that determine outcomes: how to run system demos with the people who will type the nominations rather than their managers, why lifecycle design beats big-bang cutovers, what Agile and SAFe actually contribute on a regulated trading floor (and where they get in the way), and how compliance requirements should shape architecture from day one rather than being bolted on in month eleven.",
      "If you are accountable for a delivery, as a sponsor, a product owner, a programme lead, or the engineer holding the critical path, these essays are field notes from someone who has carried that pager. Premium members get the full library.",
    ],
  },
  lifestyle: {
    title: "Personal Growth for People Who Ship",
    paragraphs: [
      "The desk teaches lessons the textbooks never mention: that attention is a portfolio, that habits compound like interest, and that the discipline which gets a power trading system live is the same discipline that gets you up a mountain road on a 350cc motorcycle. This hub gathers The Trading Narrative's essays on personal growth, written for operators rather than gurus.",
      "The essays here treat life systems the way we treat trading systems: instrument them, stress-test them, and design for failure. Deep work blocks that survive a trading-floor calendar. Annual reviews run like post-trade reconciliation. Travel that trades peak-season noise for shoulder-season signal. Money habits that make the first 100k inevitable rather than aspirational.",
      "None of this is productivity theatre. It is the same systems thinking we apply to markets and delivery, pointed inward. Read one essay, borrow one mechanism, and see if it survives contact with your real life. That is the only benchmark that matters.",
    ],
  },
};

export default function TopicPage() {
  const { slug } = useParams();
  const category = CATEGORIES.find((c) => c.slug === slug);
  const intro = TOPIC_INTROS[slug];
  const [posts, setPosts] = useState(null);

  useEffect(() => {
    setPosts(null);
    window.scrollTo(0, 0);
    api.get("/posts", { params: { category: slug } })
      .then((res) => setPosts(res.data.posts))
      .catch(() => setPosts([]));
  }, [slug]);

  if (!category || !intro) {
    return (
      <div className="container-editorial py-24 text-center">
        <h1 className="font-serif text-3xl font-semibold mb-3">Topic not found</h1>
        <Link to="/archive" className="editorial-link text-accent">Browse the archive</Link>
      </div>
    );
  }

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="topic-page">
      <Seo
        title={intro.title}
        description={intro.paragraphs[0].slice(0, 152) + "…"}
        path={`/topics/${slug}`}
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          name: intro.title,
          description: intro.paragraphs[0],
          url: `${SITE_URL}/topics/${slug}`,
          isPartOf: { "@id": `${SITE_URL}/#website` },
        }}
      />
      <div
        className="relative overflow-hidden rounded-2xl border px-6 sm:px-10 py-8 sm:py-10"
        style={{ borderColor: withAlpha(pillarAccent(slug), 0.35), backgroundColor: withAlpha(pillarAccent(slug), 0.07) }}
        data-testid="topic-header-banner"
      >
        <div
          className="absolute inset-y-0 right-0 w-3/4 sm:w-1/2 pointer-events-none"
          style={{ color: pillarAccent(slug), opacity: 0.16 }}
        >
          <PillarMotif category={slug} className="h-full w-full" />
        </div>
        <div className="relative flex items-center gap-6 sm:gap-10">
          <div className="min-w-0 flex-1">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em]" style={{ color: pillarAccent(slug) }}>
              Topic hub
            </span>
            <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3 max-w-3xl" data-testid="topic-title">
              {intro.title}
            </h1>
            <div
              className="h-1 w-16 rounded-full mt-5"
              style={{ backgroundColor: pillarAccent(slug) }}
              aria-hidden
            />
          </div>
          <img
            src={pillarMascot(slug)}
            alt={PILLAR_MASCOT_ALTS[slug]}
            className="hidden sm:block h-32 w-32 lg:h-44 lg:w-44 rounded-full object-cover shrink-0 shadow-lg"
            style={{ border: `3px solid ${withAlpha(pillarAccent(slug), 0.55)}` }}
            loading="lazy"
            data-testid={`pillar-mascot-${slug}`}
          />
        </div>
      </div>
      <div className="max-w-3xl mt-8 space-y-4">
        {intro.paragraphs.map((p, i) => (
          <p key={i} className="text-muted-foreground leading-relaxed" data-testid={`topic-intro-p${i + 1}`}>{p}</p>
        ))}
      </div>
      <div className="mt-6">
        <Link to="/archive" className="inline-flex items-center gap-1.5 text-accent font-medium text-sm hover:underline underline-offset-4" data-testid="topic-archive-link">
          Browse the full essay archive <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      <Separator className="my-10" />
      <h2 className="font-serif text-2xl font-semibold mb-6 flex items-center gap-2.5" data-testid="topic-essays-heading">
        <span className="inline-block h-5 w-1.5 rounded-full" style={{ backgroundColor: pillarAccent(slug) }} aria-hidden />
        All essays in {category.label}
      </h2>
      {posts === null ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-80 rounded-xl" />)}
        </div>
      ) : posts.length === 0 ? (
        <p className="text-muted-foreground py-12" data-testid="topic-empty">No essays under this topic yet. Check back soon.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" data-testid="topic-posts-grid">
          {posts.map((post) => <PostCard key={post.id} post={post} />)}
        </div>
      )}
    </div>
  );
}
