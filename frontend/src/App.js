import { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { trackEvent } from "@/lib/api";

import HomePage from "@/pages/HomePage";
import ArticlePage from "@/pages/ArticlePage";
import CategoryPage from "@/pages/CategoryPage";
import ArchivePage from "@/pages/ArchivePage";
import PricingPage from "@/pages/PricingPage";
import AboutPage from "@/pages/AboutPage";
import AuthPage from "@/pages/AuthPage";
import MagicVerifyPage from "@/pages/MagicVerifyPage";
import AccountPage from "@/pages/AccountPage";
import AdminPage from "@/pages/AdminPage";
import AdminEditorPage from "@/pages/AdminEditorPage";
import NotFoundPage from "@/pages/NotFoundPage";

const RouteEffects = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
    trackEvent("pageview", pathname);
  }, [pathname]);
  return null;
};

function App() {
  return (
    <HelmetProvider>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <div className="min-h-screen flex flex-col bg-background text-foreground grain-overlay">
              <RouteEffects />
              <Navbar />
              <main className="flex-1">
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/post/:slug" element={<ArticlePage />} />
                  <Route path="/category/:slug" element={<CategoryPage />} />
                  <Route path="/archive" element={<ArchivePage />} />
                  <Route path="/pricing" element={<PricingPage />} />
                  <Route path="/about" element={<AboutPage />} />
                  <Route path="/auth" element={<AuthPage />} />
                  <Route path="/auth/magic" element={<MagicVerifyPage />} />
                  <Route path="/account" element={<AccountPage />} />
                  <Route path="/admin" element={<AdminPage />} />
                  <Route path="/admin/editor" element={<AdminEditorPage />} />
                  <Route path="/admin/editor/:id" element={<AdminEditorPage />} />
                  <Route path="*" element={<NotFoundPage />} />
                </Routes>
              </main>
              <Footer />
              <Toaster position="bottom-right" richColors />
            </div>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </HelmetProvider>
  );
}

export default App;
