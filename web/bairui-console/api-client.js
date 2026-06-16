export const API = /^https?:$/.test(window.location?.protocol || "")
  ? window.location.origin
  : "http://localhost:8787";

export function apiUrl(path) {
  return `${API}${path}`;
}

export function ownerAuthHeaders() {
  let token = "";
  try {
    token = localStorage.getItem("bairui.console.ownerToken.v1") || "";
  } catch {}
  return token ? { "X-Bairui-Owner-Token": token } : {};
}

export function saveOwnerAuthToken(token) {
  try {
    const value = String(token || "").trim();
    if (value) localStorage.setItem("bairui.console.ownerToken.v1", value);
  } catch {}
}

