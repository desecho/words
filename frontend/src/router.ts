import { jwtDecode } from "jwt-decode";
import { createRouter, createWebHistory } from "vue-router";

import type { AuthProps, JWTDecoded } from "./types";
import type { RouteLocationNormalized } from "vue-router";

import { useAuthStore } from "./stores/auth";
import {
    getQueryParamAsNumber,
    getQueryParamAsString,
    isValidToken,
} from "./types/common";
import ChangePasswordView from "./views/ChangePasswordView.vue";
import LandingView from "./views/LandingView.vue";
import LoginView from "./views/LoginView.vue";
import LogoutView from "./views/LogoutView.vue";
import PreferencesView from "./views/PreferencesView.vue";
import RegisterSuccessView from "./views/RegisterSuccessView.vue";
import RegistrationView from "./views/RegistrationView.vue";
import ResetPasswordRequestView from "./views/ResetPasswordRequestView.vue";
import ResetPasswordView from "./views/ResetPasswordView.vue";
import VerifyUserView from "./views/VerifyUserView.vue";

function authProps(route: RouteLocationNormalized): AuthProps {
    return {
        signature: getQueryParamAsString(route.query.signature, ""),
        timestamp: getQueryParamAsNumber(route.query.timestamp, 0),
        userId: getQueryParamAsNumber(route.query.user_id, 0),
    };
}

export const router = createRouter({
    history: createWebHistory(),
    routes: [
        { component: LandingView, path: "/" },
        { component: LoginView, path: "/login" },
        { component: LogoutView, path: "/logout" },
        { component: RegistrationView, path: "/register" },
        { component: RegisterSuccessView, path: "/register/success" },
        {
            component: VerifyUserView,
            path: "/verify-user",
            props: authProps,
        },
        {
            component: ResetPasswordView,
            path: "/reset-password",
            props: authProps,
        },
        {
            component: ResetPasswordRequestView,
            path: "/reset-password-request",
        },
        { component: PreferencesView, path: "/preferences" },
        { component: ChangePasswordView, path: "/change-password" },
    ],
});

router.beforeEach(async (to) => {
    const privatePages = ["/preferences", "/change-password"];
    const authRequired = privatePages.includes(to.path);
    const authStore = useAuthStore();

    if (authRequired && !authStore.user.isLoggedIn) {
        return "/login";
    }

    if (authStore.user.isLoggedIn && isValidToken(authStore.user.accessToken)) {
        const decodedToken = jwtDecode<JWTDecoded>(authStore.user.accessToken);

        if (decodedToken.exp - Date.now() / 1000 < 30 * 60) {
            await authStore.refreshToken();
        }
    } else if (authStore.user.isLoggedIn) {
        return "/login";
    }

    return true;
});
