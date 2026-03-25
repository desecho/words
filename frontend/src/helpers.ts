import { router } from "./router";
import { useAuthStore } from "./stores/auth";

export const rulesHelper = {
    email: (value: string): string | true =>
        /\S+@\S+\.\S+/u.test(value) ? true : "Enter a valid email address",
    required: (value: string): string | true =>
        value.trim().length > 0 ? true : "Required",
};

export function getUrl(path: string): string {
    const baseUrl = import.meta.env.VITE_BACKEND_URL.endsWith("/")
        ? import.meta.env.VITE_BACKEND_URL
        : `${import.meta.env.VITE_BACKEND_URL}/`;

    return new URL(path, baseUrl).toString();
}

export function requireAuthenticated(): void {
    const authStore = useAuthStore();

    if (!authStore.user.isLoggedIn) {
        void router.push("/login");
    }
}
