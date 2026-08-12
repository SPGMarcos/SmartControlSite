import { createContext, useCallback, useEffect, useMemo, useState } from "react";

import { apiFetch, getAccessToken, refreshAccessToken, setAccessToken } from "../services/api.js";
import { supabase } from "../lib/supabase/client.js";
import * as authService from "../services/authService.js";

export const AuthContext = createContext(null);

const ADMIN_USER_PREVIEW_KEY = "smartcontrol_admin_user_preview";

function readPreviewFlag() {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(ADMIN_USER_PREVIEW_KEY) === "1";
}

function writePreviewFlag(active) {
  if (typeof window === "undefined") return;
  if (active) {
    localStorage.setItem(ADMIN_USER_PREVIEW_KEY, "1");
    return;
  }
  localStorage.removeItem(ADMIN_USER_PREVIEW_KEY);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [userPreviewRequested, setUserPreviewRequested] = useState(readPreviewFlag);
  const isAdmin = user?.role === "admin";
  const isUserPreviewMode = Boolean(isAdmin && userPreviewRequested);

  const loadUser = useCallback(async () => {
    try {
      if (!getAccessToken()) {
        await refreshAccessToken();
      }
      const me = await authService.getMe();
      setUser(me);
    } catch {
      setAccessToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    if (!loading && userPreviewRequested && !isAdmin) {
      writePreviewFlag(false);
      setUserPreviewRequested(false);
    }
  }, [isAdmin, loading, userPreviewRequested]);

  useEffect(() => {
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      setAccessToken(session?.access_token || null);
    });
    return () => data.subscription.unsubscribe();
  }, []);

  const login = async (payload) => {
    const loggedUser = await authService.login(payload);
    setUser(loggedUser);
    return loggedUser;
  };

  const register = async (payload) => {
    const registeredUser = await authService.register(payload);
    setUser(registeredUser);
    return registeredUser;
  };

  const logout = async () => {
    await authService.logout();
    writePreviewFlag(false);
    setUserPreviewRequested(false);
    setUser(null);
  };

  const enterUserPreviewMode = async () => {
    const status = await apiFetch("/admin/status/");
    if (!status?.admin) {
      writePreviewFlag(false);
      setUserPreviewRequested(false);
      throw new Error("Apenas administradores podem ativar a visualizacao como usuario.");
    }
    writePreviewFlag(true);
    setUserPreviewRequested(true);
    return status;
  };

  const exitUserPreviewMode = () => {
    writePreviewFlag(false);
    setUserPreviewRequested(false);
  };

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      isAdmin,
      isUserPreviewMode,
      enterUserPreviewMode,
      exitUserPreviewMode,
      login,
      register,
      logout,
      reload: loadUser
    }),
    [user, loading, isAdmin, isUserPreviewMode, loadUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
