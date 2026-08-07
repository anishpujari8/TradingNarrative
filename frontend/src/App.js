import { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/context/AuthContext";
import { BookmarkProvider } from "@/context/BookmarkContext";
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
import ResetPasswordPage from "@/pages/ResetPasswordPage";
import PaymentSuccessPage from "@/pages/PaymentSuccessPage";
import PaymentCancelPage from "@/pages/PaymentCancelPage";
import AccountPage from "@/pages/AccountPage";
import ReadingListPage from "@/pages/ReadingListPage";
import HighlightsPage from "@/pages/HighlightsPage";
import AdminPage from "@/pages/AdminPage";
import AdminEditorPage from "@/pages/AdminEditorPage";
import CommunityPage from "@/pages/CommunityPage";
import BriefingsPage from "@/pages/BriefingsPage";
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
          <BookmarkProvider>
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
                  <Route path="/auth/reset" element={<ResetPasswordPage />} />
                  <Route path="/payment/success" element={<PaymentSuccessPage />} />
                  <Route path="/payment/cancel" element={<PaymentCancelPage />} />
                  <Route path="/account" element={<AccountPage />} />
                  <Route path="/reading-list" element={<ReadingListPage />} />
                  <Route path="/highlights" element={<HighlightsPage />} />
                  <Route path="/lounge" element={<CommunityPage />} />
                  <Route path="/briefings" element={<BriefingsPage />} />
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
          </BookmarkProvider>
        </AuthProvider>
      </ThemeProvider>
    </HelmetProvider>
  );
}

export default App;
