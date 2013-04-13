// Generated by CoffeeScript 1.6.1
var get_translations;

get_translations = function(word, with_reference) {
  if (word) {
    word = $.trim(word);
    return $.post('/get_translations/', {
      word: word,
      language: language
    }, function(data) {
      var html, i, translations, _results;
      translations = data.translations;
      _results = [];
      for (i in translations) {
        html = '- ' + translations[i];
        if (with_reference) {
          html += ' [' + data.ids[i] + '] ' + '<a href="javascript:addReference(' + data.ids[i] + ', ' + getSelectionStart() + ')">Add reference</a>';
        }
        html += '<br>';
        _results.push($('#sidepanel').append(html));
      }
      return _results;
    }).error(function() {
      return displayError('Ошибка получения перевода.');
    });
  }
};
