import { apiFetch } from "./api.js";

export function getClientProfile() {
  return apiFetch("/clients/me/");
}

export function getProjects() {
  return apiFetch("/projects/");
}

export function createProject(payload, files = []) {
  const formData = new FormData();
  Object.entries(payload).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      formData.append(key, value);
    }
  });
  files.forEach((file) => formData.append("uploaded_files", file));

  return apiFetch("/projects/", {
    method: "POST",
    body: formData
  });
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

export function getPlans() {
  return apiFetch("/plans/");
}

export function createCheckoutSession(payload) {
  return apiFetch("/billing/checkout-session/", {
    method: "POST",
    body: payload
  });
}

export function createCustomerPortalSession() {
  return apiFetch("/billing/customer-portal/", {
    method: "POST"
  });
}
