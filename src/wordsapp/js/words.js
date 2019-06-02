'use strict';

import Vue from 'vue';
import axios from 'axios';

window.vm = new Vue({
  el: '#app',
  methods: {
    showTranslation: function(event) {
      var element = $(event.target)
      element.html(element.data('translation'));
    },
    markAsKnown: function(id) {
      var url = urls.words + id + '/mark-as-known/';
      axios.put(url).then(function(response) {
        $('#word' + id).remove();
      }).catch(function() {
        vm.flash(gettext('Error marking as known'), 'error', vars.flashOptions);
      });
    },
    exportToAnki: function(id) {
      var url = urls.words + id + '/export-to-anki/';
      axios.put(url).then(function(response) {
        $('#word' + id).remove();
      }).catch(function() {
        vm.flash(gettext('Error exporting to Anki'), 'error', vars.flashOptions);
      });
    },
  },
});
