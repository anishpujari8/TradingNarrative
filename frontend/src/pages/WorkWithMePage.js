import { Link } from "react-router-dom";
import { Calendar, Check, Compass, Briefcase, Wrench, IndianRupee, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Seo } from "@/components/Seo";
import { SITE_URL, SITE_NAME } from "@/lib/api";

const CALENDLY_URL = "https://calendly.com/anishpujari8/30min";

const AUDIENCES = [
  {
    icon: Briefcase,
    title: "Vendors scoping a new market",
    text: "You build or sell trading technology and want a straight read on where ETRM/CTRM buyers actually are, what they buy, and why deals stall.",
  },
  {
    icon: Compass,
    title: "Professionals entering commodity trading",
    text: "You are moving into trading, risk, or trading technology and want a map of the landscape from someone who has delivered inside it.",
  },
  {
    icon: Wrench,
    title: "Teams stuck on a delivery problem",
    text: "Your implementation has stalled, adoption is low, or the vendor and the desk are talking past each other, and you want an outside view before the next steering call.",
  },
];

const OUTCOMES = [
  "An honest outside perspective, grounded in twelve years of ETRM/CTRM delivery, not a rehearsed deck.",
  "A clear next step you can act on the same day: what to do, what to skip, who to talk to.",
  "No sales pitch. There is nothing to upsell at the end of the call.",
];

// Consulting page: 30-minute call, priced in INR, booked via Calendly.
export default function WorkWithMePage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Service",
    name: "30-minute ETRM/CTRM consulting call",
    provider: { "@type": "Person", name: "Anish Pujari", url: `${SITE_URL}/about` },
    serviceType: "Commodity trading technology consulting",
    url: `${SITE_URL}/work-with-me`,
    offers: {
      "@type": "Offer",
      price: "2999",
      priceCurrency: "INR",
      url: CALENDLY_URL,
      description: "A focused 30-minute consulting call on ETRM/CTRM, commodity trading careers, or delivery problems.",
    },
  };

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="work-with-me-page">
      <Seo
        title={`Work With Me: ETRM/CTRM Consulting Call | ${SITE_NAME}`}
        description="Book a focused 30-minute call on ETRM/CTRM, commodity trading, or a stuck delivery. Twelve years of trading systems experience, an honest outside view, and a clear next step. ₹2,999."
        path="/work-with-me"
        keywords="ETRM consultant, CTRM consulting, commodity trading advice, trading systems delivery, consulting call"
        jsonLd={jsonLd}
      />

      {/* intro / bio */}
      <div className="flex flex-col sm:flex-row items-start gap-8">
        <div className="min-w-0 flex-1">
          <span className="section-label">Consulting</span>
          <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3 leading-tight" data-testid="work-title">
            Work with me
          </h1>
          <p className="text-muted-foreground text-lg mt-5 leading-relaxed max-w-2xl">
            I have spent <strong className="text-foreground">12+ years delivering ETRM and CTRM systems</strong>,
            from power desks to metals books, on the vendor side and the buyer side. I have watched
            implementations succeed, stall, and quietly get abandoned, and I write about all of it here.
            If you want that experience pointed at your specific problem for half an hour, this is the way.
          </p>
        </div>
        <img
          src="/anish.jpg"
          alt="Anish Pujari"
          className="h-28 w-28 sm:h-36 sm:w-36 rounded-full object-cover shrink-0 shadow-lg border-2 border-accent/40"
          loading="lazy"
          data-testid="work-author-photo"
        />
      </div>

      {/* who this is for */}
      <div className="mt-14">
        <span className="section-label">Who this is for</span>
        <div className="grid sm:grid-cols-3 gap-5 mt-6">
          {AUDIENCES.map((a) => (
            <div key={a.title} className="bg-card border rounded-xl p-6" data-testid={`work-audience-${a.title.split(" ")[0].toLowerCase()}`}>
              <a.icon className="h-6 w-6 text-accent" />
              <h2 className="font-serif text-lg font-semibold mt-3">{a.title}</h2>
              <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{a.text}</p>
            </div>
          ))}
        </div>
      </div>

      {/* what you get */}
      <div className="mt-14">
        <span className="section-label">What you get from the call</span>
        <ul className="mt-6 space-y-4 max-w-2xl">
          {OUTCOMES.map((o, i) => (
            <li key={i} className="flex items-start gap-3" data-testid={`work-outcome-${i}`}>
              <Check className="h-5 w-5 text-accent shrink-0 mt-0.5" />
              <span className="text-foreground/90 leading-relaxed">{o}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* price + booking */}
      <div className="mt-14 bg-card border border-accent/30 rounded-2xl p-8 sm:p-10 max-w-2xl" data-testid="work-booking-card">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          <span className="inline-flex items-center gap-1.5 font-serif text-3xl font-semibold">
            <IndianRupee className="h-6 w-6 text-accent" /> 2,999
          </span>
          <span className="inline-flex items-center gap-1.5 text-muted-foreground text-sm">
            <Clock className="h-4 w-4" /> 30 minutes, one-on-one video call
          </span>
        </div>
        <p className="text-sm text-muted-foreground mt-4 leading-relaxed">
          Pick a slot that works for you. Come with your questions, leave with a next step.
        </p>
        <a href={CALENDLY_URL} target="_blank" rel="noopener noreferrer" data-testid="work-booking-link">
          <Button size="lg" className="mt-6 gap-2 bg-accent text-accent-foreground hover:bg-accent/90" data-testid="work-booking-button">
            <Calendar className="h-4 w-4" /> Book your 30 minutes
          </Button>
        </a>
        <p className="text-xs text-muted-foreground mt-4">
          Not sure yet? Start with the free essays in the{" "}
          <Link to="/archive" className="text-accent hover:underline" data-testid="work-archive-link">archive</Link>{" "}
          , the call will still be here.
        </p>
      </div>
    </div>
  );
}
