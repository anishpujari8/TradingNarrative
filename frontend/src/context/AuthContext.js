import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

const AuthContext = createContext(null);

// Session tokens live in a secure httpOnly cookie (ttn_session) managed by the
// backend — JavaScript never sees them (XSS protection). localStorage is only
// touched to migrate pre-cookie sessions, then wiped.
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const res = await api.get("/auth/me");
      // one-time migration: exchange a legacy localStorage token for the cookie
      if (localStorage.getItem("ttn_token")) {
        try {
          await api.post("/auth/cookie-sync");
          localStorage.removeItem("ttn_token");
        } catch (e) {
          console.debug("cookie-sync deferred:", e?.message);
        }
      }
      setUser(res.data.user);
      return res.data.user;
    } catch {
      localStorage.removeItem("ttn_token");
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  // cookie is already set by the auth endpoint response; just adopt the user
  const login = (userData) => {
    setUser(userData);
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout"); // clears the httpOnly cookie server-side
    } catch (e) {
      console.debug("logout request failed:", e?.message);
    }
    localStorage.removeItem("ttn_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
