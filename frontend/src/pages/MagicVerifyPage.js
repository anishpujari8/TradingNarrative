import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function MagicVerifyPage() {
  const [params] = useSearchParams();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const attempted = useRef(false);

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setError("Missing magic token.");
      return;
    }
    if (attempted.current) return;
    attempted.current = true;
    api
      .post("/auth/magic-link/verify", { token })
      .then((res) => {
        login(res.data.user);
        toast.success(`Signed in as ${res.data.user.email}`);
        navigate("/");
      })
      .catch((err) => setError(err?.response?.data?.detail || "This magic link is invalid or expired."));
  }, [params, login, navigate]);

  return (
    <div className="container-editorial py-28 text-center" data-testid="magic-verify-page">
      {error ? (
        <div data-testid="magic-verify-error">
          <h1 className="font-serif text-3xl font-semibold mb-3">{error}</h1>
          <Link to="/auth" className="editorial-link text-accent">Request a new magic link</Link>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4" data-testid="magic-verify-loading">
          <Loader2 className="h-8 w-8 animate-spin text-accent" />
          <p className="text-muted-foreground">Verifying your magic link…</p>
        </div>
      )}
    </div>
  );
}
