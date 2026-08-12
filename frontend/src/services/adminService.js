import { apiFetch } from "./api.js";

export function getAdminStatus() {
  return apiFetch("/admin/status/");
}

export function getAdminDashboard() {
  return apiFetch("/admin/dashboard/");
}

export function getClients() {
  return apiFetch("/clients/");
}

export function getAdminProjects() {
  return apiFetch("/projects/");
}

export function updateProject(id, payload) {
  return apiFetch(`/projects/${id}/`, {
    method: "PATCH",
    body: payload
  });
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

export function getAdminSubscriptions() {
  return apiFetch("/subscriptions/");
}

export function getAdminTransactionLogs() {
  return apiFetch("/transaction-logs/");
}

export function getAdminRequests() {
  return apiFetch("/requests/");
}
