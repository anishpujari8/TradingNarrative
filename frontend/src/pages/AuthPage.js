import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, Wand2, Info } from "lucide-react";
import { toast } from "sonner";
import { Seo } from "@/components/Seo";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function AuthPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") || "/";

  const [busy, setBusy] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [regForm, setRegForm] = useState({ name: "", email: "", password: "" });
  const [magicEmail, setMagicEmail] = useState("");
  const [magicLink, setMagicLink] = useState(null);
  const [forgotOpen, setForgotOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [resetLink, setResetLink] = useState(null);

  const doForgot = async (e) => {
    e.preventDefault();
    setBusy(true);
    setResetLink(null);
    try {
      const res = await api.post("/auth/password-reset/request", { email: forgotEmail });
      if (res.data.reset_link) {
        setResetLink(res.data.reset_link);
        toast.success("Reset link generated.");
      } else {
        toast.info(res.data.message);
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not create reset link.");
    } finally {
      setBusy(false);
    }
  };

  const doLogin = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await api.post("/auth/login", loginForm);
      login(res.data.user);
      toast.success(`Welcome back, ${res.data.user.name || "reader"}.`);
      navigate(next);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Sign in failed.");
    } finally {
      setBusy(false);
    }
  };

  const doRegister = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await api.post("/auth/register", regForm);
      login(res.data.user);
      toast.success("Account created. Welcome to The Trading Narrative.");
      navigate(next);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Registration failed.");
    } finally {
      setBusy(false);
    }
  };

  const doMagic = async (e) => {
    e.preventDefault();
    setBusy(true);
    setMagicLink(null);
    try {
      const res = await api.post("/auth/magic-link/request", { email: magicEmail });
      setMagicLink(res.data.magic_link);
      toast.success("Magic link generated.");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not create magic link.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container-editorial py-14 sm:py-20" data-testid="auth-page">
      <Seo title="Sign in" description="Sign in or create your account." path="/auth" />
      <div className="max-w-md mx-auto">
        <div className="text-center mb-8">
          <span className="section-label justify-center">Members</span>
          <h1 className="font-serif text-3xl sm:text-4xl font-semibold mt-3">Welcome to the desk</h1>
          <p className="text-muted-foreground mt-2 text-sm">Sign in to manage your subscription and unlock your library.</p>
        </div>
        <Card className="rounded-2xl shadow-[var(--shadow-soft)]">
          <CardHeader className="pb-0">
            <Tabs defaultValue="signin">
              <TabsList className="grid grid-cols-3 w-full">
                <TabsTrigger value="signin" data-testid="login-tab-password">Sign in</TabsTrigger>
                <TabsTrigger value="register" data-testid="login-tab-register">Register</TabsTrigger>
                <TabsTrigger value="magic" data-testid="login-tab-magic">Magic link</TabsTrigger>
              </TabsList>

              <TabsContent value="signin">
                <form onSubmit={doLogin} className="space-y-4 py-6">
                  <div className="space-y-1.5">
                    <Label htmlFor="login-email">Email</Label>
                    <Input id="login-email" type="email" required value={loginForm.email} onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })} data-testid="login-email-input" />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="login-password">Password</Label>
                    <Input id="login-password" type="password" required value={loginForm.password} onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })} data-testid="login-password-input" />
                  </div>
                  <Button type="submit" disabled={busy} className="w-full h-11 bg-accent text-accent-foreground hover:bg-accent/90" data-testid="login-submit-button">
                    {busy && <Loader2 className="h-4 w-4 animate-spin mr-2" />} Sign in
                  </Button>
                  <button
                    type="button"
                    onClick={() => setForgotOpen((v) => !v)}
                    className="text-xs text-muted-foreground hover:text-accent transition-colors w-full text-center"
                    data-testid="forgot-password-toggle"
                  >
                    Forgot your password?
                  </button>
                  {forgotOpen && (
                    <div className="border border-border rounded-lg p-4 space-y-3 bg-muted/30" data-testid="forgot-password-form">
                      <Label htmlFor="forgot-email" className="text-sm">Email for reset link</Label>
                      <div className="flex gap-2">
                        <Input id="forgot-email" type="email" value={forgotEmail} onChange={(e) => setForgotEmail(e.target.value)} placeholder="you@example.com" data-testid="forgot-email-input" />
                        <Button type="button" onClick={doForgot} disabled={busy || !forgotEmail.includes("@")} variant="outline" className="shrink-0" data-testid="forgot-submit-button">
                          Send
                        </Button>
                      </div>
                      {resetLink && (
                        <Alert className="border-accent/40" data-testid="reset-link-alert">
                          <Info className="h-4 w-4" />
                          <AlertTitle>Email sending is mocked (dev mode)</AlertTitle>
                          <AlertDescription className="break-all">
                            In production this arrives by email. For now:{" "}
                            <Link to={resetLink.replace(/^https?:\/\/[^/]+/, "")} className="editorial-link text-accent font-medium" data-testid="reset-link-anchor">
                              Open password reset link
                            </Link>
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  )}
                </form>
              </TabsContent>

              <TabsContent value="register">
                <form onSubmit={doRegister} className="space-y-4 py-6">
                  <div className="space-y-1.5">
                    <Label htmlFor="reg-name">Name</Label>
                    <Input id="reg-name" required value={regForm.name} onChange={(e) => setRegForm({ ...regForm, name: e.target.value })} data-testid="register-name-input" />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="reg-email">Email</Label>
                    <Input id="reg-email" type="email" required value={regForm.email} onChange={(e) => setRegForm({ ...regForm, email: e.target.value })} data-testid="register-email-input" />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="reg-password">Password (min 6 characters)</Label>
                    <Input id="reg-password" type="password" required minLength={6} value={regForm.password} onChange={(e) => setRegForm({ ...regForm, password: e.target.value })} data-testid="register-password-input" />
                  </div>
                  <Button type="submit" disabled={busy} className="w-full h-11 bg-accent text-accent-foreground hover:bg-accent/90" data-testid="register-submit-button">
                    {busy && <Loader2 className="h-4 w-4 animate-spin mr-2" />} Create account
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="magic">
                <form onSubmit={doMagic} className="space-y-4 py-6">
                  <div className="space-y-1.5">
                    <Label htmlFor="magic-email">Email</Label>
                    <Input id="magic-email" type="email" required value={magicEmail} onChange={(e) => setMagicEmail(e.target.value)} data-testid="magic-email-input" />
                  </div>
                  <Button type="submit" disabled={busy} className="w-full h-11 bg-accent text-accent-foreground hover:bg-accent/90" data-testid="magic-submit-button">
                    {busy ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Wand2 className="h-4 w-4 mr-2" />} Send me a magic link
                  </Button>
                  {magicLink && (
                    <Alert className="border-accent/40" data-testid="magic-link-alert">
                      <Info className="h-4 w-4" />
                      <AlertTitle>Email sending is mocked (dev mode)</AlertTitle>
                      <AlertDescription className="break-all">
                        In production this arrives by email. For now, click it here:{" "}
                        <Link to={magicLink.replace(/^https?:\/\/[^/]+/, "")} className="editorial-link text-accent font-medium" data-testid="magic-link-anchor">
                          Open magic sign-in link
                        </Link>
                      </AlertDescription>
                    </Alert>
                  )}
                </form>
              </TabsContent>
            </Tabs>
          </CardHeader>
          <CardContent />
        </Card>
      </div>
    </div>
  );
}
