export function getQueryParamAsNumber(value: unknown, fallback: number): number {
    if (typeof value === "string") {
        const parsedValue = Number(value);
        return Number.isFinite(parsedValue) ? parsedValue : fallback;
    }

    if (Array.isArray(value) && typeof value[0] === "string") {
        return getQueryParamAsNumber(value[0], fallback);
    }

    return fallback;
}

export function getQueryParamAsString(value: unknown, fallback: string): string {
    if (typeof value === "string") {
        return value;
    }

    if (Array.isArray(value) && typeof value[0] === "string") {
        return value[0];
    }

    return fallback;
}

export function isValidToken(token: unknown): token is string {
    return typeof token === "string" && token.length > 10;
}
