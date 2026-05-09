import { apiFetch } from "./api.js";

export function getClients() {
  return apiFetch("/clients/");
}

export function getAdminProjects() {
  return apiFetch("/projects/");
}

export function getPlans() {
  return apiFetch("/plans/");
}

export function createPlan(payload) {
  return apiFetch("/plans/", {
    method: "POST",
    body: payload
  });
}

export function getAdminPayments() {
  return apiFetch("/payments/");
}

export function getAdminRequests() {
  return apiFetch("/requests/");
}
