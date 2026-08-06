import { useEffect, useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Crown, CalendarClock, Receipt, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Seo } from "@/components/Seo";
import { api, formatDate } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function AccountPage() {
  const { user, loading, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [sub, setSub] = useState(undefined);
  const [invoices, setInvoices] = useState(null);

  const loadBilling = useCallback(() => {
    api.get("/billing/subscription").then((res) => setSub(res.data.subscription)).catch(() => setSub(null));
    api.get("/billing/invoices").then((res) => setInvoices(res.data.invoices)).catch(() => setInvoices([]));
  }, []);

  useEffect(() => {
    if (!loading && !user) {
      navigate("/auth?next=/account");
      return;
    }
    if (user) loadBilling();
  }, [user, loading, navigate, loadBilling]);

  const cancelSub = async () => {
    try {
      await api.post("/billing/cancel");
      await refreshUser();
      loadBilling();
      toast.success("Subscription canceled. You're back on the free tier.");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Cancellation failed.");
    }
  };

  if (loading || !user) {
    return <div className="container-editorial py-16"><Skeleton className="h-64 rounded-2xl max-w-2xl mx-auto" /></div>;
  }

  return (
    <div className="container-editorial py-12 sm:py-16" data-testid="account-page">
      <Seo title="Account & Billing" path="/account" />
      <div className="max-w-2xl mx-auto">
        <span className="section-label">Your account</span>
        <h1 className="font-serif text-4xl font-semibold mt-3 mb-8">Account & Billing</h1>

        {/* Profile */}
        <Card className="rounded-2xl mb-6" data-testid="account-profile-card">
          <CardHeader className="pb-2">
            <CardTitle className="font-serif text-xl flex items-center justify-between">
              Profile
              {user.is_premium ? (
                <Badge className="bg-accent/10 text-accent border border-accent/30 hover:bg-accent/10 gap-1" data-testid="account-premium-badge">
                  <Crown className="h-3 w-3" /> Premium member
                </Badge>
              ) : (
                <Badge variant="secondary" data-testid="account-free-badge">Free tier</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1.5">
            <div><span className="text-muted-foreground">Name:</span> <span data-testid="account-name">{user.name}</span></div>
            <div><span className="text-muted-foreground">Email:</span> <span data-testid="account-email">{user.email}</span></div>
            <div><span className="text-muted-foreground">Member since:</span> {formatDate(user.created_at)}</div>
            {user.role === "admin" && (
              <div className="pt-2">
                <Link to="/admin"><Button variant="outline" size="sm" data-testid="account-admin-button">Open Admin Studio</Button></Link>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Subscription */}
        <Card className="rounded-2xl mb-6" data-testid="account-subscription-card">
          <CardHeader className="pb-2">
            <CardTitle className="font-serif text-xl flex items-center gap-2">
              <CalendarClock className="h-5 w-5 text-accent" /> Subscription
            </CardTitle>
          </CardHeader>
          <CardContent>
            {sub === undefined ? (
              <Skeleton className="h-20" />
            ) : sub ? (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">Plan</span><span className="font-medium capitalize" data-testid="account-plan">{sub.plan}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Status</span><Badge className="bg-accent/10 text-accent border-accent/30 hover:bg-accent/10">{sub.status}</Badge></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Renews</span><span>{formatDate(sub.current_period_end)}</span></div>
                <Separator className="my-3" />
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" className="text-destructive border-destructive/40 hover:bg-destructive/5 hover:text-destructive" data-testid="account-cancel-button">
                      Cancel subscription
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent data-testid="cancel-dialog">
                    <AlertDialogHeader>
                      <AlertDialogTitle className="font-serif">Cancel your Premium subscription?</AlertDialogTitle>
                      <AlertDialogDescription>
                        You'll immediately lose access to premium essays, and your plan won't renew. You can re-subscribe anytime.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel data-testid="cancel-dialog-keep">Keep Premium</AlertDialogCancel>
                      <AlertDialogAction onClick={cancelSub} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" data-testid="cancel-dialog-confirm">
                        Yes, cancel
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            ) : (
              <div className="text-sm" data-testid="account-no-subscription">
                <p className="text-muted-foreground mb-4">You're on the free tier. Upgrade to unlock every essay.</p>
                <Button onClick={() => navigate("/pricing")} className="bg-accent text-accent-foreground hover:bg-accent/90" data-testid="account-upgrade-button">
                  <Sparkles className="h-4 w-4 mr-2" /> Go Premium
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Billing history */}
        <Card className="rounded-2xl" data-testid="account-billing-card">
          <CardHeader className="pb-2">
            <CardTitle className="font-serif text-xl flex items-center gap-2">
              <Receipt className="h-5 w-5 text-accent" /> Billing history
            </CardTitle>
          </CardHeader>
          <CardContent>
            {invoices === null ? (
              <Skeleton className="h-20" />
            ) : invoices.length === 0 ? (
              <p className="text-sm text-muted-foreground" data-testid="account-no-invoices">No invoices yet.</p>
            ) : (
              <Table data-testid="account-invoices-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Invoice</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invoices.map((inv) => (
                    <TableRow key={inv.id}>
                      <TableCell className="font-mono text-xs">{inv.number}</TableCell>
                      <TableCell className="capitalize">{inv.plan}</TableCell>
                      <TableCell>{formatDate(inv.created_at)}</TableCell>
                      <TableCell className="text-right">${inv.amount.toFixed(2)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
