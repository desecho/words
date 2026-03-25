import axios from "axios";

import type { AxiosError } from "axios";

import { router } from "./router";
import { useAuthStore } from "./stores/auth";
import { isValidToken } from "./types/common";
import { handleError } from "./utils/errorHandling";

let responseInterceptorId: number | null = null;
let requestInterceptorId: number | null = null;
let isRefreshingToken = false;

async function waitForRefreshToFinish(): Promise<void> {
    await new Promise<void>((resolve) => {
        function checkRefresh(): void {
            if (isRefreshingToken) {
                setTimeout(checkRefresh, 100);
            } else {
                resolve();
            }
        }

        checkRefresh();
    });
}

async function handleAuthenticationError(error: AxiosError): Promise<unknown> {
    const authStore = useAuthStore();

    if (!authStore.user.isLoggedIn) {
        void router.push("/login");
        throw error;
    }

    const errorData = error.response?.data as
        | {
              code?: string;
              detail?: string;
          }
        | undefined;

    const isTokenError =
        errorData?.code === "token_not_valid" ||
        errorData?.detail === "Given token not valid for any token type";

    if (!isTokenError) {
        handleError(error, {
            context: "Authentication error",
            showToast: false,
        });
        throw error;
    }

    if (isRefreshingToken) {
        await waitForRefreshToFinish();

        if (error.config) {
            return axios.request(error.config);
        }
    }

    // eslint-disable-next-line require-atomic-updates
    isRefreshingToken = true;

    try {
        await authStore.refreshToken();

        if (error.config) {
            return axios.request(error.config);
        }
    } catch (refreshError) {
        console.error("[Auth] Token refresh failed", refreshError);
        authStore.logout();
        void router.push("/login");
        throw refreshError;
    } finally {
        // eslint-disable-next-line require-atomic-updates
        isRefreshingToken = false;
    }

    throw error;
}

export function initAxios(): void {
    const headers: Record<string, string> = {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
    };

    const authStore = useAuthStore();
    if (authStore.user.isLoggedIn && isValidToken(authStore.user.accessToken)) {
        headers.Authorization = `Bearer ${authStore.user.accessToken}`;
    }

    axios.defaults.headers.common = headers;

    if (requestInterceptorId !== null) {
        axios.interceptors.request.eject(requestInterceptorId);
        requestInterceptorId = null;
    }

    if (responseInterceptorId !== null) {
        axios.interceptors.response.eject(responseInterceptorId);
        responseInterceptorId = null;
    }

    requestInterceptorId = axios.interceptors.request.use(
        (config) => {
            config.metadata = {
                requestId: Math.random().toString(36).slice(2),
                startTime: Date.now(),
            };

            return config;
        },
        async (error: unknown) =>
            Promise.reject(
                error instanceof Error ? error : new Error(String(error)),
            ),
    );

    responseInterceptorId = axios.interceptors.response.use(
        (response) => response,
        async (error: AxiosError) => {
            if (error.response?.status === 401) {
                return handleAuthenticationError(error);
            }

            if (
                error.code === "ERR_NETWORK" ||
                error.code === "ERR_CONNECTION_REFUSED"
            ) {
                handleError(error, {
                    context: "Backend connection failed",
                    showToast: false,
                });
            }

            return Promise.reject(
                error instanceof Error ? error : new Error(String(error)),
            );
        },
    );
}
