import { apiFetch, setAccessToken } from "./api.js";

export async function login(credentials) {
  const data = await apiFetch("/auth/login/", {
    method: "POST",
    auth: false,
    body: credentials
  });
  setAccessToken(data.access);
  return data.user;
}

export async function register(payload) {
  return apiFetch("/auth/register/", {
    method: "POST",
    auth: false,
    body: payload
  });
}

export async function logout() {
  await apiFetch("/auth/logout/", {
    method: "POST",
    body: {}
  }).catch(() => null);
  setAccessToken(null);
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
