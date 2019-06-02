'use strict';

import Vue from 'vue';
import axios from 'axios';

window.vm = new Vue({
  el: '#app',
  methods: {
    markAsExportedToAnki: function(id) {
      var url = urls.markAsExportedToAnki;
      axios.put(url).then(function(response) {}).catch(function() {
        vm.flash(gettext('Error marking as exported to Anki'), 'error', vars.flashOptions);
      });
    },
  },
});
