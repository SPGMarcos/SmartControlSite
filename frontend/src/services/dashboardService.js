import { apiFetch } from "./api.js";

export function getClientProfile() {
  return apiFetch("/clients/me/");
}

export function getProjects() {
  return apiFetch("/projects/");
}

export function getRequests() {
  return apiFetch("/requests/");
}

export function createRequest(payload) {
  return apiFetch("/requests/", {
    method: "POST",
    body: payload
  });
}

export function getSubscriptions() {
  return apiFetch("/subscriptions/");
}

export function getPayments() {
  return apiFetch("/payments/");
}

export function createCheckoutSession(payload) {
  return apiFetch("/billing/checkout-session/", {
    method: "POST",
    body: payload
  });
}
