import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Loader2, KeyRound } from "lucide-react";
import { toast } from "sonner";
import { Seo } from "@/components/Seo";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const { login } = useAuth();
  const navigate = useNavigate();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (password.length < 6) { toast.error("Password must be at least 6 characters."); return; }
    if (password !== confirm) { toast.error("Passwords don't match."); return; }
    setBusy(true);
    try {
      const res = await api.post("/auth/password-reset/confirm", { token, password });
      login(res.data.user);
      toast.success("Password updated, you're signed in.");
      navigate("/");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Reset failed. The link may have expired.");
    } finally {
      setBusy(false);
    }
  };

  if (!token) {
    return (
      <div className="container-editorial py-24 text-center" data-testid="reset-password-invalid">
        <h1 className="font-serif text-3xl font-semibold mb-3">Missing reset token</h1>
        <Link to="/auth" className="editorial-link text-accent">Request a new reset link</Link>
      </div>
    );
  }

  return (
    <div className="container-editorial py-14 sm:py-20" data-testid="reset-password-page">
      <Seo title="Reset password" path="/auth/reset" />
      <Card className="max-w-md mx-auto rounded-2xl shadow-[var(--shadow-soft)]">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center mb-2">
            <KeyRound className="h-5 w-5 text-accent" />
          </div>
          <h1 className="font-serif text-2xl font-semibold">Choose a new password</h1>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4 pt-2">
            <div className="space-y-1.5">
              <Label htmlFor="new-password">New password (min 6 characters)</Label>
              <Input id="new-password" type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} data-testid="reset-password-input" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="confirm-password">Confirm password</Label>
              <Input id="confirm-password" type="password" required value={confirm} onChange={(e) => setConfirm(e.target.value)} data-testid="reset-password-confirm-input" />
            </div>
            <Button type="submit" disabled={busy} className="w-full h-11 bg-accent text-accent-foreground hover:bg-accent/90" data-testid="reset-password-submit-button">
              {busy && <Loader2 className="h-4 w-4 animate-spin mr-2" />} Update password & sign in
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
