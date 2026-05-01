import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api, setAuthHandlers } from "../api/client";
import { isSupabaseEnabled } from "../lib/backendMode";
import { signInWithPassword, signOut, signUp, supabase } from "../lib/supabase";
import { decodeJwt, isJwtExpired } from "../utils/jwt";

const STORAGE_KEY = "reconx_auth";
const AuthContext = createContext(null);

function isStoredAuthShapeValid(value) {
  return Boolean(
    value &&
      typeof value.accessToken === "string" &&
      value.accessToken &&
      typeof value.refreshToken === "string" &&
      value.refreshToken,
  );
}

function loadStoredAuth() {
  if (isSupabaseEnabled) {
    localStorage.removeItem(STORAGE_KEY);
    return null;
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    if (
      !isStoredAuthShapeValid(parsed) ||
      isJwtExpired(parsed.accessToken) ||
      isJwtExpired(parsed.refreshToken)
    ) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return isStoredAuthShapeValid(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(loadStoredAuth);
  const [backendAuth, setBackendAuth] = useState(null);
  const [supabaseSession, setSupabaseSession] = useState(null);
  const [isBootstrapping, setIsBootstrapping] = useState(isSupabaseEnabled);

  async function exchangeSupabaseAccessToken(session) {
    if (!session?.access_token) {
      setBackendAuth(null);
      return null;
    }
    const { data } = await api.post("/auth/supabase/exchange", {
      access_token: session.access_token,
    });
    const nextAuth = {
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
    };
    setBackendAuth(nextAuth);
    return nextAuth;
  }

  useEffect(() => {
    if (isSupabaseEnabled) {
      return undefined;
    }
    if (auth) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [auth]);

  useEffect(() => {
    if (!isSupabaseEnabled) {
      return undefined;
    }

    let mounted = true;
    localStorage.removeItem(STORAGE_KEY);

    supabase.auth.getSession().then(async ({ data }) => {
      if (mounted) {
        const session = data.session || null;
        setSupabaseSession(session);
        if (session) {
          await exchangeSupabaseAccessToken(session).catch(() => {
            if (mounted) setBackendAuth(null);
          });
        }
        setIsBootstrapping(false);
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (mounted) {
        setSupabaseSession(session || null);
        if (session) {
          exchangeSupabaseAccessToken(session)
            .catch(() => {
              if (mounted) setBackendAuth(null);
            })
            .finally(() => {
              if (mounted) setIsBootstrapping(false);
            });
        } else {
          setBackendAuth(null);
          setIsBootstrapping(false);
        }
      }
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  const login = async (tokens) => {
    if (isSupabaseEnabled) {
      const result = await signInWithPassword(tokens);
      setSupabaseSession(result.session || null);
      await exchangeSupabaseAccessToken(result.session);
      return;
    }

    setAuth({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
    });
  };

  const register = async (tokens) => {
    if (isSupabaseEnabled) {
      const result = await signUp(tokens);
      if (result.session) {
        setSupabaseSession(result.session);
        await exchangeSupabaseAccessToken(result.session);
      } else {
        const signInResult = await signInWithPassword(tokens);
        setSupabaseSession(signInResult.session || null);
        await exchangeSupabaseAccessToken(signInResult.session);
      }
      return;
    }
    return login(tokens);
  };

  const logout = async () => {
    if (isSupabaseEnabled) {
      await signOut();
      setSupabaseSession(null);
      setBackendAuth(null);
      return;
    }
    setAuth(null);
  };

  const refreshTokens = async () => {
    if (!auth?.refreshToken) {
      throw new Error("No refresh token available");
    }
    const { data } = await api.post("/auth/refresh", { refresh_token: auth.refreshToken });
    const nextAuth = {
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
    };
    setAuth(nextAuth);
    return nextAuth;
  };

  useEffect(() => {
    if (isSupabaseEnabled) {
      setAuthHandlers({
        getTokens: () => backendAuth,
        refreshTokens: async () => {
          const { data } = await supabase.auth.getSession();
          return exchangeSupabaseAccessToken(data.session);
        },
        logout: () => {
          logout().catch(() => {});
        },
      });
      return;
    }
    setAuthHandlers({
      getTokens: () => auth,
      refreshTokens,
      logout,
    });
  }, [auth, backendAuth]);

  useEffect(() => {
    if (isSupabaseEnabled || !auth?.refreshToken) {
      return;
    }

    let cancelled = false;
    refreshTokens().catch(() => {
      if (!cancelled) {
        setAuth(null);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo(() => {
    if (isSupabaseEnabled) {
      const user = supabaseSession?.user || null;
      const role = user?.user_metadata?.role || "user";
      return {
        auth: supabaseSession,
        accessToken: backendAuth?.accessToken ?? null,
        refreshToken: backendAuth?.refreshToken ?? null,
        supabaseAccessToken: supabaseSession?.access_token ?? null,
        user: user ? { id: user.id, role, email: user.email || null } : null,
        isAuthenticated: Boolean(user),
        isBootstrapping,
        role,
        isAdmin: role === "admin",
        login,
        register,
        logout,
      };
    }

    let role = null;
    let userId = null;
    if (auth?.accessToken) {
      const decoded = decodeJwt(auth.accessToken);
      role = decoded?.role || null;
      userId = decoded?.sub ? Number(decoded.sub) : null;
    }
    return {
      auth,
      accessToken: auth?.accessToken ?? null,
      refreshToken: auth?.refreshToken ?? null,
      user: userId ? { id: userId, role } : null,
      isAuthenticated: Boolean(auth?.accessToken),
      isBootstrapping: false,
      role,
      isAdmin: role === "admin",
      login,
      register,
      logout,
    };
  }, [auth, isBootstrapping, supabaseSession]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
