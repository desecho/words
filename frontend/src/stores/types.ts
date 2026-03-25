export interface UserStore {
    accessToken?: string;
    isLoggedIn: boolean;
    refreshToken?: string;
    username?: string;
}

export interface TokenData {
    access: string;
    refresh: string;
}

export interface TokenRefreshData {
    access: string;
}
