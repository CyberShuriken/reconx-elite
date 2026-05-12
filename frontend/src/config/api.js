/**
 * API Configuration
 * Centralized configuration for API base URL and WebSocket URL
 */

import { firstFrontendEnv } from "./env.js";

function normalizeBaseUrl(url) {
  return (url || "").replace(/\/+$/, "");
}

function resolveDefaultBackendBaseUrl() {
  if (typeof window !== "undefined") {
    const { hostname } = window.location;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return `${window.location.protocol || "http:"}//${hostname}:8000`;
    }
    return "";
  }
  const protocol = "http:";
  const hostname = "localhost";
  return `${protocol}//${hostname}:8000`;
}

// Prefer VITE_API_URL, but keep VITE_API_BASE_URL for existing deployments.
export const API_BASE_URL = normalizeBaseUrl(
  firstFrontendEnv("VITE_API_URL", "VITE_API_BASE_URL") || resolveDefaultBackendBaseUrl(),
);

// WebSocket URL can be explicit, otherwise it follows the configured API origin.
export const WS_BASE_URL = normalizeBaseUrl(
  firstFrontendEnv("VITE_WS_URL") ||
    API_BASE_URL.replace(/^http:/, "ws:").replace(/^https:/, "wss:"),
);

export { normalizeBaseUrl, resolveDefaultBackendBaseUrl };
