// Styles
// eslint-disable-next-line import/no-unassigned-import
import "@mdi/font/css/materialdesignicons.css";
// eslint-disable-next-line import/no-unassigned-import
import "vuetify/styles";

import { createVuetify } from "vuetify";

export const WORDS_LIGHT_THEME = "wordsLight";
export const WORDS_DARK_THEME = "wordsDark";
export const WORDS_THEME_STORAGE_KEY = "words-theme";

export type WordsThemeName =
    | typeof WORDS_LIGHT_THEME
    | typeof WORDS_DARK_THEME;

function isWordsThemeName(value: string | null): value is WordsThemeName {
    return value === WORDS_LIGHT_THEME || value === WORDS_DARK_THEME;
}

export function applyDocumentTheme(themeName: WordsThemeName): void {
    if (typeof document === "undefined") {
        return;
    }

    document.documentElement.dataset.theme =
        themeName === WORDS_DARK_THEME ? "dark" : "light";
}

export function persistTheme(themeName: WordsThemeName): void {
    if (typeof localStorage === "undefined") {
        return;
    }

    localStorage.setItem(WORDS_THEME_STORAGE_KEY, themeName);
}

export function resolveInitialTheme(): WordsThemeName {
    if (typeof window === "undefined") {
        return WORDS_LIGHT_THEME;
    }

    const storedTheme = localStorage.getItem(WORDS_THEME_STORAGE_KEY);
    if (isWordsThemeName(storedTheme)) {
        return storedTheme;
    }

    if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
        return WORDS_DARK_THEME;
    }

    return WORDS_LIGHT_THEME;
}

const initialTheme = resolveInitialTheme();
applyDocumentTheme(initialTheme);

export default createVuetify({
    defaults: {
        VBtn: {
            style: [{ textTransform: "none" }],
        },
        VCard: {
            rounded: "xl",
        },
        VTextField: {
            variant: "outlined",
        },
    },
    theme: {
        defaultTheme: initialTheme,
        themes: {
            [WORDS_LIGHT_THEME]: {
                colors: {
                    background: "#f5efe6",
                    error: "#b75b4b",
                    primary: "#8b4d36",
                    secondary: "#265f55",
                    surface: "#fffaf3",
                    "surface-bright": "#ffffff",
                    "surface-variant": "#eadbc8",
                    warning: "#c59240",
                },
                dark: false,
            },
            [WORDS_DARK_THEME]: {
                colors: {
                    background: "#120f0d",
                    error: "#f09b8a",
                    primary: "#e39f72",
                    secondary: "#7cb7aa",
                    surface: "#1d1713",
                    "surface-bright": "#2a221d",
                    "surface-variant": "#352c26",
                    warning: "#d4a75f",
                },
                dark: true,
            },
        },
    },
});
