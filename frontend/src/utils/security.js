export function cleanText(value) {
  const parsed = new DOMParser().parseFromString(String(value || ""), "text/html");
  return parsed.body.textContent.trim();
}

export function isStrongEnoughPassword(value) {
  return String(value || "").length >= 10;
}
