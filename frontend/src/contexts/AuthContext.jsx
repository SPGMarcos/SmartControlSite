import { createContext, useCallback, useEffect, useMemo, useState } from "react";

import { getAccessToken, refreshAccessToken, setAccessToken } from "../services/api.js";
import { supabase } from "../lib/supabase/client.js";
import * as authService from "../services/authService.js";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

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
    setUser(null);
  };

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      isAdmin: user?.role === "admin",
      login,
      register,
      logout,
      reload: loadUser
    }),
    [user, loading, loadUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
