import axios from "axios";

export const SESSION_EXPIRED_MESSAGE = "Your session expired. Please sign in again.";

const configuredBackendBaseUrl = process.env.VITE_API_BASE_URL;

function normalizeBaseUrl(url) {
  return (url || "").replace(/\/+$/, "");
}

function resolveDefaultBackendBaseUrl() {
  if (typeof window === "undefined") {
    return "http://localhost:8000";
  }

  return `http://${window.location.hostname}:8000`;
}

const backendBaseUrl = normalizeBaseUrl(
  configuredBackendBaseUrl || resolveDefaultBackendBaseUrl(),
);

let getTokens = () => null;
let refreshTokens = async () => {
  throw new Error("No refresh handler configured");
};
let logout = () => {};
let refreshPromise = null;

export const api = axios.create({
  baseURL: backendBaseUrl,
  withCredentials: false,
});

/** FastAPI may return `detail` as a string or a Pydantic validation list */
export function formatApiErrorDetail(detail) {
  if (detail == null) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) =>
        item && typeof item === "object" && item.msg ? item.msg : JSON.stringify(item),
      )
      .join("; ");
  }
  if (typeof detail === "object" && detail.msg) return detail.msg;
  return String(detail);
}

export function setAuthHandlers(handlers) {
  getTokens = handlers.getTokens;
  refreshTokens = handlers.refreshTokens;
  logout = handlers.logout;
}

api.interceptors.request.use((config) => {
  const tokens = getTokens?.();
  if (tokens?.accessToken) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${tokens.accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error;
    const isAuthEndpoint =
      config?.url?.includes("/auth/refresh") ||
      config?.url?.includes("/auth/login") ||
      config?.url?.includes("/auth/register");
    if (!response || response.status !== 401 || config?._retry || isAuthEndpoint) {
      throw error;
    }

    try {
      if (!refreshPromise) {
        refreshPromise = refreshTokens().finally(() => {
          refreshPromise = null;
        });
      }
      const tokens = await refreshPromise;
      config._retry = true;
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${tokens.accessToken}`;
      return api(config);
    } catch (_refreshError) {
      logout();
      if (error.response) {
        error.response.data = {
          ...(error.response.data || {}),
          detail: SESSION_EXPIRED_MESSAGE,
        };
      }
      throw error;
    }
  },
);

export { backendBaseUrl };
