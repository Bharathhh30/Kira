import { useAuthStore } from "@/store/authStore";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

interface RequestOptions extends RequestInit {
  json?: any;
}

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

async function apiFetch(
  endpoint: string,
  options: RequestOptions = {}
): Promise<Response> {
  const { accessToken } = useAuthStore.getState();

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.json) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const fetchOptions: RequestInit = {
    ...options,
    headers,
    credentials: "include", // Ensure HttpOnly cookies are sent and received
  };

  if (options.json) {
    fetchOptions.body = JSON.stringify(options.json);
  }

  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, fetchOptions);

  if (
    response.status === 401 &&
    !endpoint.includes("/auth/login") &&
    !endpoint.includes("/auth/refresh")
  ) {
    if (!isRefreshing) {
      isRefreshing = true;
      const { setAuth, clearAuth } = useAuthStore.getState();
      try {
        const refreshResponse = await fetch(`${BASE_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });

        if (refreshResponse.ok) {
          const data = await refreshResponse.json();

          // Fetch user info with new token
          const meResponse = await fetch(`${BASE_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${data.access_token}` },
          });
          if (meResponse.ok) {
            const meData = await meResponse.json();
            setAuth(meData, data.access_token);
            isRefreshing = false;
            onRefreshed(data.access_token);
          } else {
            throw new Error("Failed to get profile during refresh");
          }
        } else {
          throw new Error("Refresh failed");
        }
      } catch (err) {
        isRefreshing = false;
        clearAuth();
        return response;
      }
    }

    // Queue failed requests to retry after refresh completes
    const retryOriginalRequest = new Promise<Response>((resolve) => {
      subscribeTokenRefresh((newToken) => {
        headers.set("Authorization", `Bearer ${newToken}`);
        resolve(fetch(`${BASE_URL}${endpoint}`, fetchOptions));
      });
    });

    return retryOriginalRequest;
  }

  return response;
}

export const api = {
  get: (endpoint: string, options?: RequestOptions) =>
    apiFetch(endpoint, { method: "GET", ...options }),
  post: (endpoint: string, json?: any, options?: RequestOptions) =>
    apiFetch(endpoint, { method: "POST", json, ...options }),
  put: (endpoint: string, json?: any, options?: RequestOptions) =>
    apiFetch(endpoint, { method: "PUT", json, ...options }),
  delete: (endpoint: string, options?: RequestOptions) =>
    apiFetch(endpoint, { method: "DELETE", ...options }),
};
