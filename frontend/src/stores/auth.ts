import axios from "axios";
import { jwtDecode } from "jwt-decode";
import { defineStore } from "pinia";

import type { JWTDecoded } from "../types";
import type { TokenData, TokenRefreshData, UserStore } from "./types";

import { initAxios } from "../axios";
import { getUrl } from "../helpers";
import { router } from "../router";
import { isValidToken } from "../types/common";

const userDefault: UserStore = {
    isLoggedIn: false,
};

export const useAuthStore = defineStore("auth", {
    actions: {
        async login(username: string, password: string): Promise<void> {
            const response = await axios.post(getUrl("token/"), {
                password,
                username,
            });
            const data = response.data as TokenData;

            this.user = {
                accessToken: data.access,
                isLoggedIn: true,
                refreshToken: data.refresh,
                username,
            };

            initAxios();
            void router.push("/study");
        },
        logout(): void {
            this.user = { isLoggedIn: false };
            localStorage.removeItem("user");
            delete axios.defaults.headers.common.Authorization;
            initAxios();
            void router.push("/");
        },
        async refreshToken(): Promise<void> {
            if (!isValidToken(this.user.refreshToken)) {
                this.logout();
                return;
            }

            const decodedToken = jwtDecode<JWTDecoded>(this.user.refreshToken);
            if (decodedToken.exp < Date.now() / 1000) {
                this.logout();
                return;
            }

            const response = await axios.post(getUrl("token/refresh/"), {
                refresh: this.user.refreshToken,
            });
            const data = response.data as TokenRefreshData;

            this.user.accessToken = data.access;
            initAxios();
        },
    },
    persist: true,
    state: () => ({
        user: userDefault,
    }),
});
