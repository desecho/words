import axios, { AxiosHeaders } from "axios";

import type { AxiosError, AxiosRequestConfig } from "axios";

import { router } from "./router";
import { useAuthStore } from "./stores/auth";
import { isValidToken } from "./types/common";
import { handleError } from "./utils/errorHandling";

let responseInterceptorId: number | null = null;
let requestInterceptorId: number | null = null;
let isRefreshingToken = false;

type AxiosHeadersInput = Parameters<typeof AxiosHeaders.from>[0];

function requestPath(config: AxiosRequestConfig): string {
    if (config.url === undefined) {
        return "";
    }

    try {
        return new URL(config.url, config.baseURL ?? "http://localhost").pathname;
    } catch {
        return config.url;
    }
}

function isPublicTokenRequest(config: AxiosRequestConfig | undefined): boolean {
    if (config === undefined) {
        return false;
    }

    const path = requestPath(config);
    return path === "/token/" || path === "/token/refresh/";
}

function currentAccessToken(): string | undefined {
    const authStore = useAuthStore();

    if (authStore.user.isLoggedIn && isValidToken(authStore.user.accessToken)) {
        return authStore.user.accessToken;
    }

    return undefined;
}

function syncAuthorizationHeader(config: AxiosRequestConfig): void {
    const headers = AxiosHeaders.from(config.headers as AxiosHeadersInput);
    const accessToken = currentAccessToken();

    if (accessToken !== undefined && !isPublicTokenRequest(config)) {
        headers.set("Authorization", `Bearer ${accessToken}`);
    } else {
        headers.delete("Authorization");
    }

    config.headers = headers;
}

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
    const requestConfig = error.config;

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

    if (
        requestConfig === undefined ||
        requestConfig.hasRetriedAuthentication === true ||
        isPublicTokenRequest(requestConfig)
    ) {
        authStore.logout();
        void router.push("/login");
        throw error;
    }

    if (isRefreshingToken) {
        await waitForRefreshToFinish();

        if (
            authStore.user.isLoggedIn &&
            isValidToken(authStore.user.accessToken)
        ) {
            requestConfig.hasRetriedAuthentication = true;
            syncAuthorizationHeader(requestConfig);
            return axios.request(requestConfig);
        }

        throw error;
    }

    requestConfig.hasRetriedAuthentication = true;
    // eslint-disable-next-line require-atomic-updates
    isRefreshingToken = true;

    try {
        await authStore.refreshToken();

        if (
            !authStore.user.isLoggedIn ||
            !isValidToken(authStore.user.accessToken)
        ) {
            throw error;
        }

        syncAuthorizationHeader(requestConfig);
        return axios.request(requestConfig);
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
            syncAuthorizationHeader(config);

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
