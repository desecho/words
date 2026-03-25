// eslint-disable-next-line import/no-unassigned-import
import "x-axios-progress-bar/dist/nprogress.css";
// eslint-disable-next-line import/no-unassigned-import
import "./styles/styles.scss";

import { createPinia } from "pinia";
import piniaPluginPersistedstate from "pinia-plugin-persistedstate";
import { createApp } from "vue";
import { loadProgressBar } from "x-axios-progress-bar";

import App from "./App.vue";
import { initAxios } from "./axios";
import vuetify from "./plugins/vuetify";
import { router } from "./router";

loadProgressBar();

const pinia = createPinia();
pinia.use(piniaPluginPersistedstate);

createApp(App).use(vuetify).use(pinia).use(router).mount("#app");

initAxios();
