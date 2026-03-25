export interface AuthProps {
    userId: number;
    timestamp: number;
    signature: string;
}

export interface JWTDecoded {
    exp: number;
    token_type: string;
}

export interface UserPreferences {
    email: string;
    username: string;
}
