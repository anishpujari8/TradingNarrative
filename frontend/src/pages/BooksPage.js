import { useEffect, useState } from "react";
import { ExternalLink, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Seo } from "@/components/Seo";
import { api, SITE_URL, SITE_NAME } from "@/lib/api";

export default function BooksPage() {
  const [books, setBooks] = useState(null);

  useEffect(() => {
    api.get("/books").then((res) => setBooks(res.data.books)).catch(() => setBooks([]));
  }, []);

  const jsonLd = books?.length
    ? {
        "@context": "https://schema.org",
        "@type": "ItemList",
        name: `${SITE_NAME} Bookshelf`,
        url: `${SITE_URL}/books`,
        itemListElement: books.map((b, i) => ({
          "@type": "ListItem",
          position: i + 1,
          item: { "@type": "Book", name: b.title, author: { "@type": "Person", name: b.author }, url: b.buy_url },
        })),
      }
    : undefined;

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="books-page">
      <Seo
        title="Books: Trading & Systems Reading List"
        description="Books worth a trader's time, recommended by Anish Pujari: trading, risk, market mechanics, and building better systems. Starting with How Trading Can Make You Money."
        path="/books"
        keywords="trading books, commodity trading reading list, How Trading Can Make You Money, Anish Pujari book"
        jsonLd={jsonLd}
      />
      <span className="section-label">Bookshelf</span>
      <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3 max-w-3xl" data-testid="books-title">
        Books worth a trader's time
      </h1>
      <p className="text-muted-foreground mt-5 max-w-2xl leading-relaxed">
        A short, honest shelf: books on trading, risk, and building systems that actually hold up.
        No filler recommendations, if it is here, it earned the spot.
      </p>

      {books === null && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-10">
          {[0, 1, 2].map((i) => <Skeleton key={i} className="h-96 rounded-xl" />)}
        </div>
      )}

      {books?.length === 0 && (
        <div className="border border-dashed border-border rounded-xl p-12 text-center mt-10" data-testid="books-empty-state">
          <BookOpen className="h-8 w-8 mx-auto text-muted-foreground" />
          <p className="text-muted-foreground mt-3">The shelf is being stocked. Check back soon.</p>
        </div>
      )}

      {books?.length > 0 && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-10" data-testid="books-grid">
          {books.map((b) => (
            <article
              key={b.id}
              className="bg-card border border-border rounded-xl overflow-hidden flex flex-col hover:border-accent/50 transition-colors duration-200"
              data-testid={`book-card-${b.id}`}
            >
              <div className="aspect-[4/3] overflow-hidden bg-muted">
                {b.cover_image ? (
                  <img src={b.cover_image} alt={`${b.title} by ${b.author}, book cover`} loading="lazy" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                    <BookOpen className="h-10 w-10" />
                  </div>
                )}
              </div>
              <div className="p-5 flex flex-col flex-1">
                {b.featured && (
                  <Badge className="w-fit bg-accent/10 text-accent border border-accent/30 hover:bg-accent/10 font-mono text-[10px] uppercase tracking-wider mb-2 rounded-md">
                    By the author
                  </Badge>
                )}
                <h2 className="font-serif text-xl font-semibold leading-snug">{b.title}</h2>
                <p className="font-mono text-xs text-muted-foreground mt-1">by {b.author}</p>
                {b.description && (
                  <p className="text-sm text-muted-foreground mt-3 leading-relaxed flex-1">{b.description}</p>
                )}
                <a href={b.buy_url} target="_blank" rel="noopener noreferrer" className="mt-5" data-testid={`book-buy-${b.id}`}>
                  <Button className="w-full gap-2 bg-accent text-accent-foreground hover:bg-accent/90">
                    Buy on Amazon <ExternalLink className="h-4 w-4" />
                  </Button>
                </a>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
