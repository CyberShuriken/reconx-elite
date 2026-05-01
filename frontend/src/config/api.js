/**
 * API Configuration
 * Centralized configuration for API base URL and WebSocket URL
 */

function normalizeBaseUrl(url) {
  return (url || "").replace(/\/+$/, "");
}

// Read the Railway backend URL from the build-time env var.
// Falls back to localhost:8000 only in local development (when VITE_API_URL is unset).
export const API_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_API_URL || "http://localhost:8000"
);

// WebSocket URL - can be explicitly set via VITE_WS_URL or derived from API_BASE_URL
export const WS_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_WS_URL || 
  API_BASE_URL.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:')
);
