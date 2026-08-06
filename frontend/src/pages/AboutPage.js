import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Seo } from "@/components/Seo";
import { NewsletterForm } from "@/components/NewsletterForm";

export default function AboutPage() {
  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="about-page">
      <Seo title="About" description="The story behind The Trading Narrative and its author, Jordan Hale." path="/about" />
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 items-start">
        <div className="lg:col-span-5">
          <div className="rounded-2xl overflow-hidden border border-border shadow-[var(--shadow-float)] card-img-zoom">
            <img
              src="https://images.pexels.com/photos/10209456/pexels-photo-10209456.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
              alt="Jordan Hale, author of The Trading Narrative"
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
              I'm Jordan Hale — a former fintech operator and trader who spent a decade watching
              brilliant people make terrible decisions because nobody translated the numbers into
              narrative. The Trading Narrative is my answer to that gap.
            </p>
            <p>
              This publication covers four things I care about obsessively: technology and the
              businesses being built on it, personal finance and investing without the noise,
              the systems behind a well-designed life, and travel that changes how you think
              rather than just where you've been.
            </p>
            <p>
              Every essay follows the same rule: it must be something I'd send to a close friend
              who asked a hard question. No filler, no engagement bait, no ten-item listicles.
              One idea, argued properly, with the homework done.
            </p>
            <p>
              Free subscribers get a full essay every week and previews of premium work.
              Premium members get everything: the full library, ad-free reading, and early
              access to new pieces before they're public.
            </p>
          </div>
          <Separator className="my-8" />
          <div className="bg-muted/40 border border-border rounded-2xl p-6">
            <h3 className="font-serif text-xl font-semibold mb-1">Join the readers</h3>
            <p className="text-sm text-muted-foreground mb-4">Get the next narrative in your inbox.</p>
            <NewsletterForm source="about" testId="about-newsletter-form" />
            <div className="mt-4">
              <Link to="/pricing">
                <Button variant="outline" className="w-full sm:w-auto" data-testid="about-pricing-button">Explore Premium</Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
