import { create } from "zustand";

export interface User {
	id: string;
	email: string;
	name: string;
	is_active: boolean;
	created_at: string;
	updated_at: string;
}

interface AuthState {
	user: User | null;
	accessToken: string | null;
	setAuth: (user: User, accessToken: string) => void;
	setAccessToken: (accessToken: string | null) => void;
	clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
	user: null,
	accessToken: null,
	setAuth: (user, accessToken) => set({ user, accessToken }),
	setAccessToken: (accessToken) => set({ accessToken }),
	clearAuth: () => set({ user: null, accessToken: null }),
}));
