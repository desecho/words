// Styles
// eslint-disable-next-line import/no-unassigned-import
import "@mdi/font/css/materialdesignicons.css";
// eslint-disable-next-line import/no-unassigned-import
import "vuetify/styles";

import { createVuetify } from "vuetify";

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
        defaultTheme: "words",
        themes: {
            words: {
                colors: {
                    background: "#f5efe6",
                    primary: "#8b4d36",
                    secondary: "#265f55",
                    surface: "#fffaf3",
                    "surface-bright": "#ffffff",
                    "surface-variant": "#eadbc8",
                },
                dark: false,
            },
        },
    },
});
