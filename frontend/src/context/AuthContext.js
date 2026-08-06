import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem("ttn_token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return null;
    }
    try {
      const res = await api.get("/auth/me");
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

  const login = (token, userData) => {
    localStorage.setItem("ttn_token", token);
    setUser(userData);
  };

  const logout = () => {
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
