const PRODUCTION_API_URL = "https://smartcontrolsite.onrender.com/api";

function getDefaultApiUrl() {
  if (typeof window === "undefined") return PRODUCTION_API_URL;
  return ["localhost", "127.0.0.1"].includes(window.location.hostname) ? "/api" : PRODUCTION_API_URL;
}

const API_BASE_URL = normalizeApiUrl(
  (typeof window !== "undefined" && window.__API_BASE_URL) ||
    import.meta.env.VITE_API_URL ||
    getDefaultApiUrl()
);
const ACCESS_TOKEN_KEY = "smartcontrol_access";

let accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
let csrfReady = false;
let csrfToken = "";

function normalizeApiUrl(value) {
  const fallback = "/api";
  const url = String(value || fallback).trim() || fallback;
  return url.replace(/\/+$/, "");
}

export function setAccessToken(token) {
  accessToken = token || null;
  if (token) {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

export function getAccessToken() {
  return accessToken;
}

function getCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

async function ensureCsrf() {
  if (csrfReady) return;
  const response = await fetch(`${API_BASE_URL}/csrf/`, {
    method: "GET",
    credentials: "include"
  });
  if (!response.ok) {
    throw new Error("Nao foi possivel preparar a seguranca da sessao.");
  }
  const data = await response.json().catch(() => ({}));
  csrfToken = data.csrfToken || decodeURIComponent(getCookie("csrftoken") || "");
  csrfReady = true;
}

function getCsrfToken() {
  return csrfToken || decodeURIComponent(getCookie("csrftoken") || "");
}

async function refreshAccessToken() {
  await ensureCsrf();
  const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken()
    }
  });

  if (!response.ok) {
    setAccessToken(null);
    throw new Error("Sessao expirada.");
  }

  const data = await response.json();
  setAccessToken(data.access);
  return data.access;
}

export async function apiFetch(path, options = {}) {
  const method = options.method || "GET";
  const headers = new Headers(options.headers || {});
  const hasBody = options.body !== undefined;

  if (hasBody && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (accessToken && options.auth !== false) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  if (!["GET", "HEAD", "OPTIONS"].includes(method.toUpperCase())) {
    await ensureCsrf();
    headers.set("X-CSRFToken", getCsrfToken());
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    method,
    credentials: "include",
    headers,
    body: hasBody && !(options.body instanceof FormData) ? JSON.stringify(options.body) : options.body
  });

  if (response.status === 401 && options.retry !== false && options.auth !== false) {
    const token = await refreshAccessToken();
    headers.set("Authorization", `Bearer ${token}`);
    return apiFetch(path, { ...options, headers, retry: false });
  }

  if (response.status === 204) return null;

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const fieldError = Object.values(data)
      .flat()
      .find((item) => typeof item === "string");
    throw new Error(data.detail || data.non_field_errors?.[0] || fieldError || "Nao foi possivel concluir a operacao.");
  }
  return data;
}

export { refreshAccessToken };
export { API_BASE_URL };
