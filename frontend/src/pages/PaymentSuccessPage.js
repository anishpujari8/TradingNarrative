import { useEffect, useRef, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, CheckCircle2, Clock, XCircle, Crown } from "lucide-react";
import { Seo } from "@/components/Seo";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const MAX_ATTEMPTS = 10;

export default function PaymentSuccessPage() {
  const [params] = useSearchParams();
  const { refreshUser } = useAuth();
  const [state, setState] = useState("verifying"); // verifying | success | pending | expired | error
  const attempts = useRef(0);
  const started = useRef(false);

  useEffect(() => {
    const sessionId = params.get("session_id");
    if (!sessionId) {
      setState("error");
      return;
    }
    if (started.current) return;
    started.current = true;

    const poll = async () => {
      attempts.current += 1;
      try {
        const res = await api.get(`/payments/status/${sessionId}`);
        if (res.data.payment_status === "paid") {
          await refreshUser();
          setState("success");
          return;
        }
        if (res.data.status === "expired") {
          setState("expired");
          return;
        }
      } catch {
        setState("error");
        return;
      }
      if (attempts.current >= MAX_ATTEMPTS) {
        setState("pending");
        return;
      }
      setTimeout(poll, 2000);
    };
    poll();
  }, [params, refreshUser]);

  return (
    <div className="container-editorial py-20 sm:py-28" data-testid="payment-success-page">
      <Seo title="Payment status" path="/payment/success" />
      <Card className="max-w-md mx-auto rounded-2xl shadow-[var(--shadow-float)]">
        <CardContent className="p-10 text-center">
          {state === "verifying" && (
            <div data-testid="payment-verifying">
              <Loader2 className="h-10 w-10 animate-spin text-accent mx-auto mb-4" />
              <h1 className="font-serif text-2xl font-semibold">Confirming your payment…</h1>
              <p className="text-muted-foreground text-sm mt-2">This usually takes a few seconds. Don't close this page.</p>
            </div>
          )}
          {state === "success" && (
            <div data-testid="payment-success">
              <div className="mx-auto w-14 h-14 rounded-full bg-accent/10 flex items-center justify-center mb-4">
                <CheckCircle2 className="h-7 w-7 text-accent" />
              </div>
              <h1 className="font-serif text-3xl font-semibold">Welcome to Premium</h1>
              <p className="text-muted-foreground mt-2">
                Payment confirmed, every essay is now unlocked, ad-free, with early access.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center mt-7">
                <Link to="/archive">
                  <Button className="bg-accent text-accent-foreground hover:bg-accent/90 h-11 w-full sm:w-auto" data-testid="payment-success-read-button">
                    <Crown className="h-4 w-4 mr-2" /> Start reading
                  </Button>
                </Link>
                <Link to="/account">
                  <Button variant="outline" className="h-11 w-full sm:w-auto" data-testid="payment-success-account-button">View account</Button>
                </Link>
              </div>
            </div>
          )}
          {state === "pending" && (
            <div data-testid="payment-pending">
              <Clock className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
              <h1 className="font-serif text-2xl font-semibold">Payment still processing</h1>
              <p className="text-muted-foreground text-sm mt-2">
                Your payment is taking longer than usual. Check your account in a minute, access activates automatically once it clears.
              </p>
              <Link to="/account"><Button variant="outline" className="mt-6">Go to account</Button></Link>
            </div>
          )}
          {(state === "expired" || state === "error") && (
            <div data-testid="payment-error">
              <XCircle className="h-10 w-10 text-destructive mx-auto mb-4" />
              <h1 className="font-serif text-2xl font-semibold">
                {state === "expired" ? "Checkout session expired" : "Something went wrong"}
              </h1>
              <p className="text-muted-foreground text-sm mt-2">No charge was made. You can try again anytime.</p>
              <Link to="/pricing"><Button className="mt-6 bg-accent text-accent-foreground hover:bg-accent/90">Back to pricing</Button></Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
