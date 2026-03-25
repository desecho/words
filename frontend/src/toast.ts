import { useToast } from "vue-toast-notification";
// eslint-disable-next-line import/no-unassigned-import
import "vue-toast-notification/dist/theme-default.css";

export const $toast = useToast({
    duration: 2500,
    position: "bottom-right",
});
