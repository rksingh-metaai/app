import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

import { storage } from "@/src/utils/storage";
import { api, TOKEN_KEY } from "@/src/api/client";
import { LangCode } from "@/src/i18n/translations";

export type User = {
  id: string;
  name: string;
  email: string;
  language: string;
  currency: string;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, language: LangCode) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const token = await storage.secureGet<string>(TOKEN_KEY, "");
        if (token) {
          const me = await api.get("/auth/me");
          setUser(me);
        }
      } catch {
        await storage.secureRemove(TOKEN_KEY);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data = await api.post("/auth/login", { email, password });
    await storage.secureSet(TOKEN_KEY, data.token);
    setUser(data.user);
  }, []);

  const register = useCallback(
    async (name: string, email: string, password: string, language: LangCode) => {
      const data = await api.post("/auth/register", { name, email, password, language });
      await storage.secureSet(TOKEN_KEY, data.token);
      setUser(data.user);
    },
    [],
  );

  const logout = useCallback(async () => {
    await storage.secureRemove(TOKEN_KEY);
    setUser(null);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const me = await api.get("/auth/me");
      setUser(me);
    } catch {
      // ignore
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
