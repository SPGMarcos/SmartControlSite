import { apiFetch, getRefreshToken, setAccessToken, setRefreshToken } from "./api.js";
import { supabase } from "../lib/supabase/client.js";

async function persistSupabaseSession(data) {
  if (!data.access || !data.refresh) return;
  await supabase.auth.setSession({
    access_token: data.access,
    refresh_token: data.refresh
  });
}

export async function login(credentials) {
  const data = await apiFetch("/auth/login/", {
    method: "POST",
    auth: false,
    body: credentials
  });
  await persistSupabaseSession(data);
  setAccessToken(data.access);
  setRefreshToken(data.refresh);
  return data.user;
}

export async function register(payload) {
  const data = await apiFetch("/auth/register/", {
    method: "POST",
    auth: false,
    body: payload
  });
  if (data.access) {
    setAccessToken(data.access);
  }
  if (data.refresh) {
    setRefreshToken(data.refresh);
  }
  await persistSupabaseSession(data);
  return data.user || data;
}

export async function logout() {
  await apiFetch("/auth/logout/", {
    method: "POST",
    body: getRefreshToken() ? { refresh: getRefreshToken() } : {}
  }).catch(() => null);
  await supabase.auth.signOut().catch(() => null);
  setAccessToken(null);
  setRefreshToken(null);
}

export async function getMe() {
  return apiFetch("/auth/me/");
}

export async function requestPasswordReset(email) {
  return apiFetch("/auth/password-reset/", {
    method: "POST",
    auth: false,
    body: { email }
  });
}

export async function confirmPasswordReset(payload) {
  return apiFetch("/auth/password-reset/confirm/", {
    method: "POST",
    auth: false,
    body: payload
  });
}
