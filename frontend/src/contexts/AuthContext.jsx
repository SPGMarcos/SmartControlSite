import { createContext, useCallback, useEffect, useMemo, useState } from "react";

import { getAccessToken, refreshAccessToken, setAccessToken } from "../services/api.js";
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

  const login = async (payload) => {
    const loggedUser = await authService.login(payload);
    setUser(loggedUser);
    return loggedUser;
  };

  const register = async (payload) => {
    await authService.register(payload);
    return login({ email: payload.email, password: payload.password });
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
