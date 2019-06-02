'use strict';

import Vue from 'vue';
import VueFlashMessage from 'vue-flash-message';
import VueCookie from 'vue-cookies';
window.vars = {};
vars.flashOptions = {
  timeout: 1500,
  important: true,
};
window.urls = {};

Vue.use(VueFlashMessage);
Vue.use(VueCookie);
Vue.options.delimiters = ['[[', ']]'];
