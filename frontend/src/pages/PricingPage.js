import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Check, X, Crown, Loader2, Sparkles, Star } from "lucide-react";
import { toast } from "sonner";
import { Seo } from "@/components/Seo";
import { api, trackEvent, getPreferredCurrency, setPreferredCurrency, formatINR } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const FEATURES = [
  { name: "Free weekly essays", free: true, premium: true, founding: true },
  { name: "Newsletter delivery", free: true, premium: true, founding: true },
  { name: "Preview of premium essays", free: true, premium: true, founding: true },
  { name: "Full premium essay library", free: false, premium: true, founding: true },
  { name: "Weekly premium briefings", free: false, premium: true, founding: true },
  { name: "20-second narration previews", free: true, premium: true, founding: true },
  { name: "Full essay audio narrations", free: false, premium: true, founding: true },
  { name: "Ad-free reading", free: false, premium: true, founding: true },
  { name: "Early access to new posts", free: false, premium: true, founding: true },
  { name: "Premium member badge", free: false, premium: true, founding: true },
  { name: "Direct email access to Anish", free: false, premium: false, founding: true },
  { name: "Quarterly members Q&A call", free: false, premium: false, founding: true },
  { name: "Founding member shoutout", free: false, premium: false, founding: true },
];

// Anchored in USD, localized round numbers for INR (per growth plan)
const PRICING = {
  monthly: { usd: "$1.04", inr: formatINR(99), per: "/month", label: "Monthly" },
  annual: { usd: "$10.50", inr: formatINR(999), per: "/year", label: "Annual" },
  founding_monthly: { usd: "$4.80", inr: formatINR(458), per: "/month", label: "Founding Member Monthly" },
  founding: { usd: "$57.69", inr: formatINR(5499), per: "/year", label: "Founding Member" },
};

export default function PricingPage() {
  const { user, refreshUser, logout } = useAuth();
  const navigate = useNavigate();
  const [annual, setAnnual] = useState(true);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [redirecting, setRedirecting] = useState(false);
  const [mockMode, setMockMode] = useState(false);
  const [autoRenew, setAutoRenew] = useState(false);
  const [currency, setCurrency] = useState(getPreferredCurrency());
  const [razorpayEnabled, setRazorpayEnabled] = useState(false);
  const [razorpayAutopay, setRazorpayAutopay] = useState(false);
  const [rzpConfirm, setRzpConfirm] = useState(false);
  const [rzpBusy, setRzpBusy] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState("annual");
  const [earlyBird, setEarlyBird] = useState(null); // first-50 launch promo

  const changeCurrency = (c) => {
    setCurrency(c);
    setPreferredCurrency(c);
  };

  useEffect(() => {
    api.get("/billing/config").then((res) => {
      setMockMode(res.data.mock_mode);
      setAutoRenew(res.data.auto_renew);
      setRazorpayEnabled(res.data.razorpay_enabled);
      setRazorpayAutopay(!!res.data.razorpay_autopay);
    }).catch(() => {});
    api.get("/billing/early-bird").then((res) => setEarlyBird(res.data)).catch(() => {});
  }, []);

  const isINR = currency === "inr";
  const premiumPlan = annual ? "annual" : "monthly";
  const foundingPlan = annual ? "founding" : "founding_monthly";
  const priceFor = (planId) => (isINR ? PRICING[planId].inr : PRICING[planId].usd);
  const selected = PRICING[selectedPlan];
  const monthlyEquiv = isINR ? formatINR(83) : "$0.88";
  // EARLY BIRD: first 50 premium subscribers get a discounted first period
  const ebActive = !!earlyBird?.active && !user?.is_premium;
  const ebPlan = earlyBird?.plans?.[premiumPlan];
  const ebPrice = ebPlan ? (isINR ? formatINR(ebPlan.amount_inr) : `$${ebPlan.amount.toFixed(2)}`) : null;

  // Session-expiry aware error handling: a stale token must never dead-end at "Not authenticated"
  const handleCheckoutError = (err, fallback) => {
    const status = err?.response?.status;
    if (status === 401 || status === 403) {
      logout();
      toast.error("Your session has expired, please sign in again to go Premium.");
      navigate("/auth?next=/pricing");
      return;
    }
    toast.error(err?.response?.data?.detail || fallback);
  };

  const razorpayCheckout = async (planId) => {
    setRedirecting(true);
    try {
      const res = await api.post("/billing/razorpay/checkout", { plan: planId });
      if (res.data.mock) {
        setRzpConfirm(res.data);
        setRedirecting(false);
        return;
      }
      // REAL Razorpay checkout (activates once keys are configured)
      await new Promise((resolve, reject) => {
        if (window.Razorpay) return resolve();
        const script = document.createElement("script");
        script.src = "https://checkout.razorpay.com/v1/checkout.js";
        script.onload = resolve;
        script.onerror = reject;
        document.body.appendChild(script);
      });
      const rzpOptions = {
        key: res.data.razorpay_key_id,
        name: res.data.name,
        description: res.data.description,
        handler: async (resp) => {
          try {
            await api.post("/billing/razorpay/verify", {
              order_id: res.data.ref_id,
              payment_id: resp.razorpay_payment_id,
              signature: resp.razorpay_signature,
            });
            await refreshUser();
            toast.success("Welcome aboard! Every essay is now unlocked.");
            navigate("/account");
          } catch {
            toast.error("Payment verification failed. Contact support.");
          }
        },
        modal: { ondismiss: () => setRedirecting(false) },
      };
      if (res.data.kind === "subscription") {
        // UPI Autopay recurring mandate
        rzpOptions.subscription_id = res.data.subscription_id;
      } else {
        rzpOptions.order_id = res.data.order_id;
        rzpOptions.amount = res.data.amount;
        rzpOptions.currency = res.data.currency;
      }
      const rzp = new window.Razorpay(rzpOptions);
      rzp.open();
    } catch (err) {
      handleCheckoutError(err, "Could not start Razorpay checkout.");
      setRedirecting(false);
    }
  };

  const confirmRazorpayMock = async () => {
    setRzpBusy(true);
    try {
      await api.post("/billing/razorpay/verify", { order_id: rzpConfirm.order_id });
      await refreshUser();
      setRzpConfirm(false);
      toast.success("Welcome aboard! Every essay is now unlocked.");
      navigate("/account");
    } catch (err) {
      handleCheckoutError(err, "Checkout failed. Try again.");
    } finally {
      setRzpBusy(false);
    }
  };

  const startCheckout = async (planId) => {
    setSelectedPlan(planId);
    trackEvent("subscribe_cta_click", "/pricing", { plan: planId });
    if (!user) {
      toast.info("Create an account or sign in to go Premium.");
      navigate("/auth?next=/pricing");
      return;
    }
    if (user.is_premium) {
      toast.success("You're already Premium!");
      return;
    }
    if (isINR) {
      razorpayCheckout(planId);
      return;
    }
    if (mockMode) {
      setConfirmOpen(true);
      return;
    }
    // Real Stripe checkout
    setRedirecting(true);
    try {
      const res = await api.post("/billing/checkout", { plan: planId, origin_url: window.location.origin });
      if (res.data.checkout_url) {
        window.location.href = res.data.checkout_url;
        return;
      }
      toast.error("Could not start checkout. Try again.");
      setRedirecting(false);
    } catch (err) {
      handleCheckoutError(err, "Checkout failed. Try again.");
      setRedirecting(false);
    }
  };

  const confirmCheckout = async () => {
    setBusy(true);
    try {
      await api.post("/billing/checkout", { plan: selectedPlan, origin_url: window.location.origin });
      await refreshUser();
      setConfirmOpen(false);
      toast.success("Welcome aboard! Every essay is now unlocked.");
      navigate("/account");
    } catch (err) {
      handleCheckoutError(err, "Checkout failed. Try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="pricing-page">
      <Seo title="Pricing" description="Free vs Premium, unlock every essay on The Trading Narrative." path="/pricing" />
      <div className="text-center max-w-2xl mx-auto">
        <span className="section-label justify-center">Membership</span>
        <h1 className="font-serif text-4xl sm:text-5xl font-semibold mt-3">Read everything. Own your edge.</h1>
        <p className="text-muted-foreground text-lg mt-4">
          Start free. Upgrade when you want the full library, premium briefings, audio narrations, and early access.
        </p>

        <div className="flex items-center justify-center gap-3 mt-8">
          <span className={`text-sm ${!annual ? "font-semibold" : "text-muted-foreground"}`} data-testid="pricing-billing-monthly">Monthly</span>
          <Switch checked={annual} onCheckedChange={setAnnual} data-testid="pricing-billing-toggle" aria-label="Toggle annual billing" />
          <span className={`text-sm ${annual ? "font-semibold" : "text-muted-foreground"}`} data-testid="pricing-billing-annual">Annual</span>
          <Badge className="bg-accent/10 text-accent border border-accent/30 hover:bg-accent/10" data-testid="pricing-savings-badge">2 months free</Badge>
        </div>

        <div className="flex items-center justify-center gap-1 mt-4">
          <div className="inline-flex border border-border rounded-full p-0.5 bg-card" data-testid="pricing-currency-toggle">
            <button
              onClick={() => changeCurrency("usd")}
              className={`px-4 py-1.5 rounded-full text-xs font-mono transition-colors ${!isINR ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:text-foreground"}`}
              data-testid="pricing-currency-usd"
            >
              $ USD
            </button>
            <button
              onClick={() => changeCurrency("inr")}
              className={`px-4 py-1.5 rounded-full text-xs font-mono transition-colors ${isINR ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:text-foreground"}`}
              data-testid="pricing-currency-inr"
            >
              ₹ INR
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mt-10">
        {/* FREE */}
        <Card className="rounded-2xl" data-testid="pricing-free-card">
          <CardHeader className="pb-2">
            <h3 className="font-serif text-2xl font-semibold">Free</h3>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-semibold" data-testid="pricing-free-amount">{isINR ? "₹0" : "$0"}</span>
              <span className="text-muted-foreground text-sm">forever</span>
            </div>
            <p className="text-xs text-muted-foreground pt-1">Core essays and newsletter, build your edge for free.</p>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3 text-sm mt-2">
              {FEATURES.slice(0, 7).map((f) => (
                <li key={f.name} className="flex items-start gap-2">
                  {f.free ? <Check className="h-4 w-4 text-accent mt-0.5 shrink-0" /> : <X className="h-4 w-4 text-muted-foreground/50 mt-0.5 shrink-0" />}
                  <span className={f.free ? "" : "text-muted-foreground/60 line-through"}>{f.name}</span>
                </li>
              ))}
            </ul>
            <Button variant="outline" className="w-full mt-6 h-11" onClick={() => navigate(user ? "/archive" : "/auth")} data-testid="pricing-free-button">
              {user ? "Keep reading free essays" : "Create a free account"}
            </Button>
          </CardContent>
        </Card>

        {/* PREMIUM */}
        <Card className="rounded-2xl border-accent/50 relative shadow-[var(--shadow-float)]" data-testid="pricing-premium-card">
          <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent text-accent-foreground hover:bg-accent whitespace-nowrap" data-testid="pricing-premium-badge">
            {ebActive ? `Early bird · ${earlyBird.remaining} of ${earlyBird.spots} spots left` : "Most popular"}
          </Badge>
          <CardHeader className="pb-2">
            <h3 className="font-serif text-2xl font-semibold flex items-center gap-2">
              Premium <Crown className="h-5 w-5 text-accent" />
            </h3>
            <div className="flex items-baseline gap-2">
              {ebActive && ebPrice ? (
                <>
                  <span className="text-4xl font-semibold text-accent" data-testid="pricing-premium-amount">{ebPrice}</span>
                  <span className="text-lg text-muted-foreground line-through" data-testid="pricing-premium-regular-price">{priceFor(premiumPlan)}</span>
                  <span className="text-muted-foreground text-sm">{PRICING[premiumPlan].per}</span>
                </>
              ) : (
                <>
                  <span className="text-4xl font-semibold" data-testid="pricing-premium-amount">{priceFor(premiumPlan)}</span>
                  <span className="text-muted-foreground text-sm">{PRICING[premiumPlan].per}</span>
                </>
              )}
            </div>
            {ebActive && ebPrice && (
              <p className="text-xs text-accent font-medium" data-testid="pricing-early-bird-note">
                Early bird price for your first {annual ? "year" : "month"}, then {priceFor(premiumPlan)}{PRICING[premiumPlan].per}.
              </p>
            )}
            {annual && <p className="text-xs text-muted-foreground font-mono">That's {monthlyEquiv}/month</p>}
          </CardHeader>
          <CardContent>
            <ul className="space-y-3 text-sm mt-2">
              {FEATURES.filter((f) => f.premium).map((f) => (
                <li key={f.name} className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                  <span>{f.name}</span>
                </li>
              ))}
            </ul>
            <Button
              className="w-full mt-6 h-11 bg-accent text-accent-foreground hover:bg-accent/90"
              onClick={() => startCheckout(premiumPlan)}
              disabled={redirecting}
              data-testid="pricing-checkout-button"
            >
              {redirecting && !selectedPlan.startsWith("founding") ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
              {user?.is_premium ? "You're Premium" : `Go Premium ${annual ? "annual" : "monthly"}`}
            </Button>
            {mockMode ? (
              <p className="text-[11px] text-muted-foreground font-mono mt-3 text-center" data-testid="pricing-mock-notice">
                Test mode, Stripe-ready, no card required yet.
              </p>
            ) : (
              <p className="text-[11px] text-muted-foreground font-mono mt-3 text-center" data-testid="pricing-stripe-notice">
                {isINR
                  ? razorpayEnabled
                    ? razorpayAutopay
                      ? "UPI Autopay · cards · netbanking via Razorpay · renews automatically · cancel anytime"
                      : `UPI · cards · netbanking via Razorpay · ${annual ? "365" : "30"}-day pass · Test mode`
                    : "UPI · cards · netbanking via Razorpay · MOCKED until keys are added"
                  : autoRenew
                    ? "Secure Stripe checkout · renews automatically · cancel anytime"
                    : `Secure Stripe checkout · Test mode · ${annual ? "365" : "30"}-day pass · card 4242 4242 4242 4242`}
              </p>
            )}
          </CardContent>
        </Card>

        {/* FOUNDING MEMBER */}
        <Card className="rounded-2xl border-foreground/20 relative" data-testid="pricing-founding-card">
          <Badge variant="secondary" className="absolute -top-3 left-1/2 -translate-x-1/2">Limited</Badge>
          <CardHeader className="pb-2">
            <h3 className="font-serif text-2xl font-semibold flex items-center gap-2">
              Founding Member <Star className="h-5 w-5 text-accent" />
            </h3>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-semibold" data-testid="pricing-founding-amount">{priceFor(foundingPlan)}</span>
              <span className="text-muted-foreground text-sm">{PRICING[foundingPlan].per}</span>
            </div>
            <p className="text-xs text-muted-foreground pt-1">Back the publication early, get everything, plus direct access.</p>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3 text-sm mt-2">
              <li className="flex items-start gap-2">
                <Check className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                <span className="font-medium">Everything in Premium</span>
              </li>
              {FEATURES.filter((f) => f.founding && !f.premium).map((f) => (
                <li key={f.name} className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                  <span>{f.name}</span>
                </li>
              ))}
            </ul>
            <Button
              variant="outline"
              className="w-full mt-6 h-11 border-accent/60 text-accent hover:bg-accent/10 hover:text-accent"
              onClick={() => startCheckout(foundingPlan)}
              disabled={redirecting}
              data-testid="pricing-founding-button"
            >
              {redirecting && selectedPlan.startsWith("founding") ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Star className="h-4 w-4 mr-2" />}
              {user?.is_premium ? "You're Premium" : "Become a Founding Member"}
            </Button>
            <p className="text-[11px] text-muted-foreground font-mono mt-3 text-center">
              Direct access · quarterly Q&A · founding shoutout
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Comparison table */}
      <div className="max-w-4xl mx-auto mt-14">
        <h2 className="font-serif text-2xl font-semibold mb-4 text-center">Compare tiers</h2>
        <div className="border border-border rounded-xl overflow-hidden bg-card">
          <Table data-testid="pricing-comparison-table">
            <TableHeader>
              <TableRow>
                <TableHead>Feature</TableHead>
                <TableHead className="text-center">Free</TableHead>
                <TableHead className="text-center">Premium</TableHead>
                <TableHead className="text-center">Founding</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {FEATURES.map((f) => (
                <TableRow key={f.name}>
                  <TableCell className="text-sm">{f.name}</TableCell>
                  <TableCell className="text-center">{f.free ? <Check className="h-4 w-4 text-accent inline" /> : <X className="h-4 w-4 text-muted-foreground/40 inline" />}</TableCell>
                  <TableCell className="text-center">{f.premium ? <Check className="h-4 w-4 text-accent inline" /> : <X className="h-4 w-4 text-muted-foreground/40 inline" />}</TableCell>
                  <TableCell className="text-center"><Check className="h-4 w-4 text-accent inline" /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Razorpay mock checkout dialog */}
      <Dialog open={!!rzpConfirm} onOpenChange={(o) => !o && setRzpConfirm(false)}>
        <DialogContent data-testid="razorpay-mock-dialog">
          <DialogHeader>
            <DialogTitle className="font-serif text-2xl">Razorpay checkout (mocked)</DialogTitle>
            <DialogDescription>
              UPI, cards, and netbanking activate the moment Razorpay keys are added. For now this test checkout grants Premium instantly, no payment collected.
            </DialogDescription>
          </DialogHeader>
          <div className="bg-muted/40 border border-border rounded-lg p-4 flex justify-between items-center">
            <div>
              <div className="font-medium">{selected.label} (INR)</div>
              <div className="text-xs text-muted-foreground font-mono">{PRICING[selectedPlan].per === "/month" ? "30" : "365"}-day pass · cancel anytime</div>
            </div>
            <div className="text-2xl font-semibold">{priceFor(selectedPlan)}<span className="text-sm text-muted-foreground">{selected.per}</span></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRzpConfirm(false)}>Cancel</Button>
            <Button onClick={confirmRazorpayMock} disabled={rzpBusy} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="razorpay-mock-confirm-button">
              {rzpBusy ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
              Activate Premium
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Mock checkout dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent data-testid="checkout-dialog">
          <DialogHeader>
            <DialogTitle className="font-serif text-2xl">Confirm your subscription</DialogTitle>
            <DialogDescription>
              {mockMode
                ? "Test-mode checkout (Stripe-ready). No card will be charged, your Premium access activates instantly."
                : "You'll be redirected to Stripe to complete payment."}
            </DialogDescription>
          </DialogHeader>
          <div className="bg-muted/40 border border-border rounded-lg p-4 flex justify-between items-center">
            <div>
              <div className="font-medium">{selected.label}</div>
              <div className="text-xs text-muted-foreground font-mono">Renews every {PRICING[selectedPlan].per === "/month" ? "month" : "year"} · cancel anytime</div>
            </div>
            <div className="text-2xl font-semibold">{priceFor(selectedPlan)}<span className="text-sm text-muted-foreground">{selected.per}</span></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)} data-testid="checkout-cancel-button">Cancel</Button>
            <Button onClick={confirmCheckout} disabled={busy} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="checkout-confirm-button">
              {busy ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
              Activate Premium
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
