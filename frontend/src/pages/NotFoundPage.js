import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Seo } from "@/components/Seo";

export default function NotFoundPage() {
  return (
    <div className="container-editorial py-28 text-center" data-testid="not-found-page">
      <Seo title="Page not found" />
      <span className="section-label justify-center">404</span>
      <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-4">This page wandered off</h1>
      <p className="text-muted-foreground mt-3 mb-8">The story you're looking for doesn't exist, but plenty of good ones do.</p>
      <Link to="/">
        <Button className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="not-found-home-button">Back to the homepage</Button>
      </Link>
    </div>
  );
}
