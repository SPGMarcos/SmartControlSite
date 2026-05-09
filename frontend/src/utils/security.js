export function cleanText(value) {
  const parsed = new DOMParser().parseFromString(String(value || ""), "text/html");
  return parsed.body.textContent.trim();
}

export function isStrongEnoughPassword(value) {
  const checks = getPasswordChecks(value);
  return checks.every((item) => item.valid);
}

export function getPasswordChecks(value) {
  const password = String(value || "");
  return [
    { id: "length", label: "Minimo de 10 caracteres", valid: password.length >= 10 },
    { id: "uppercase", label: "Uma letra maiuscula", valid: /[A-Z]/.test(password) },
    { id: "lowercase", label: "Uma letra minuscula", valid: /[a-z]/.test(password) },
    { id: "number", label: "Um numero", valid: /\d/.test(password) },
    { id: "special", label: "Um caractere especial", valid: /[^A-Za-z0-9]/.test(password) }
  ];
}
