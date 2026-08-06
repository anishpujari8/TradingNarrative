import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowLeft, CircleSlash } from "lucide-react";
import { Seo } from "@/components/Seo";

export default function PaymentCancelPage() {
  return (
    <div className="container-editorial py-20 sm:py-28" data-testid="payment-cancel-page">
      <Seo title="Checkout canceled" path="/payment/cancel" />
      <Card className="max-w-md mx-auto rounded-2xl">
        <CardContent className="p-10 text-center">
          <CircleSlash className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
          <h1 className="font-serif text-2xl font-semibold">Checkout canceled</h1>
          <p className="text-muted-foreground text-sm mt-2">
            No charge was made. Premium will be here whenever you're ready.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center mt-7">
            <Link to="/pricing">
              <Button className="bg-accent text-accent-foreground hover:bg-accent/90 h-11 w-full sm:w-auto" data-testid="payment-cancel-retry-button">Back to pricing</Button>
            </Link>
            <Link to="/">
              <Button variant="outline" className="h-11 w-full sm:w-auto" data-testid="payment-cancel-home-button">
                <ArrowLeft className="h-4 w-4 mr-2" /> Keep reading free essays
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
