import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import type { User } from "@/store/authStore";

export function useAuth() {
  const queryClient = useQueryClient();
  const { setAuth, setAccessToken, clearAuth, user, accessToken } =
    useAuthStore();

  const registerMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post("/auth/register", data);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Registration failed");
      }
      return response.json();
    },
  });

  const loginMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post("/auth/login", data);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Login failed");
      }
      const tokenData = await response.json();

      // Fetch user profile immediately using the new access token
      const meResponse = await api.get("/auth/me", {
        headers: { Authorization: `Bearer ${tokenData.access_token}` },
      });
      if (!meResponse.ok) {
        throw new Error("Failed to load user profile");
      }
      const meData = await meResponse.json();
      setAuth(meData, tokenData.access_token);
      return meData;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });

  const logoutMutation = useMutation({
    mutationFn: async () => {
      await api.post("/auth/logout");
      clearAuth();
      queryClient.setQueryData(["me"], null);
    },
  });

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      // 1. If we have the access token in memory, fetch the user profile directly
      if (accessToken) {
        const response = await api.get("/auth/me");
        if (response.ok) {
          return response.json() as Promise<User>;
        }
      }

      // 2. Otherwise, attempt a silent refresh on startup using the HttpOnly cookie
      try {
        const refreshResponse = await api.post("/auth/refresh");
        if (refreshResponse.ok) {
          const data = await refreshResponse.json();
          setAccessToken(data.access_token);

          const meResponse = await api.get("/auth/me", {
            headers: { Authorization: `Bearer ${data.access_token}` },
          });
          if (meResponse.ok) {
            const meData = await meResponse.json();
            setAuth(meData, data.access_token);
            return meData;
          }
        }
      } catch (err) {
        // Safe to ignore, user is not logged in / guest
      }

      clearAuth();
      return null;
    },
    retry: false,
    staleTime: Infinity,
  });

  return {
    user: user || meQuery.data || null,
    isLoading: meQuery.isLoading,
    register: registerMutation,
    login: loginMutation,
    logout: logoutMutation,
  };
}
