import { Link } from "react-router-dom";
import { Separator } from "@/components/ui/separator";
import { NewsletterForm } from "@/components/NewsletterForm";
import { CATEGORIES } from "@/lib/api";
import { Linkedin, Instagram } from "lucide-react";

export const Footer = () => (
  <footer className="border-t border-border bg-muted/40 mt-20">
    <div className="container-editorial py-12 sm:py-16">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-10">
        <div className="md:col-span-5">
          <div className="flex items-center gap-2.5 mb-3">
            <img src="/logo192.png" alt="The Trading Narrative logo" className="w-9 h-9" />
            <span className="font-serif text-xl font-semibold">The Trading Narrative</span>
          </div>
          <p className="text-sm text-muted-foreground max-w-sm mb-5">
            Sharp narratives on markets, technology, and a life well designed. One thoughtful
            essay at a time — straight to your inbox.
          </p>
          <NewsletterForm source="footer" compact testId="footer-newsletter-form" />
        </div>
        <div className="md:col-span-3">
          <h4 className="font-mono text-xs uppercase tracking-widest text-muted-foreground mb-4">Pillars</h4>
          <ul className="space-y-2.5">
            {CATEGORIES.map((c) => (
              <li key={c.slug}>
                <Link to={`/category/${c.slug}`} className="text-sm hover:text-accent transition-colors" data-testid={`footer-category-${c.slug}`}>
                  {c.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div className="md:col-span-2">
          <h4 className="font-mono text-xs uppercase tracking-widest text-muted-foreground mb-4">Site</h4>
          <ul className="space-y-2.5">
            <li><Link to="/archive" className="text-sm hover:text-accent transition-colors">Archive</Link></li>
            <li><Link to="/pricing" className="text-sm hover:text-accent transition-colors">Pricing</Link></li>
            <li><Link to="/about" className="text-sm hover:text-accent transition-colors">About</Link></li>
            <li><Link to="/auth" className="text-sm hover:text-accent transition-colors">Sign in</Link></li>
          </ul>
        </div>
        <div className="md:col-span-2">
          <h4 className="font-mono text-xs uppercase tracking-widest text-muted-foreground mb-4">Follow</h4>
          <div className="flex gap-3">
            <a href="https://www.linkedin.com" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn" className="p-2 border border-border rounded-lg hover:border-accent hover:text-accent transition-colors" data-testid="footer-linkedin-link">
              <Linkedin className="h-4 w-4" />
            </a>
            <a href="https://www.instagram.com" target="_blank" rel="noopener noreferrer" aria-label="Instagram" className="p-2 border border-border rounded-lg hover:border-accent hover:text-accent transition-colors" data-testid="footer-instagram-link">
              <Instagram className="h-4 w-4" />
            </a>
          </div>
        </div>
      </div>
      <Separator className="my-8" />
      <div className="flex flex-col sm:flex-row justify-between gap-2 text-xs text-muted-foreground font-mono">
        <span>© {new Date().getFullYear()} The Trading Narrative. All rights reserved.</span>
        <span>Made with conviction, published with care.</span>
      </div>
    </div>
  </footer>
);
