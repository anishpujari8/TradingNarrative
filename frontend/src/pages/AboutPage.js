import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Seo } from "@/components/Seo";
import { Linkedin, Instagram } from "lucide-react";
import { NewsletterForm } from "@/components/NewsletterForm";
import { FoundingWall } from "@/components/FoundingWall";

export default function AboutPage() {
  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="about-page">
      <Seo title="About" description="The story behind The Trading Narrative and its author, Anish Pujari." path="/about" />
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
              comes from managing complexity — stakeholders, teams, ambiguity — rather than just
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
              <a href="https://www.instagram.com" target="_blank" rel="noopener noreferrer">
                <Button variant="outline" className="gap-2" data-testid="about-instagram-button"><Instagram className="h-4 w-4" /> Follow on Instagram</Button>
              </a>
            </div>
          </div>
        </div>
      </div>

      <FoundingWall />
    </div>
  );
}
