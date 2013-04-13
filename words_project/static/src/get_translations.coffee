get_translations = (word, with_reference) ->
  if word
    word = $.trim(word)
    $.post('/get_translations/', {word: word, language: language},
      (data) ->
        translations = data.translations
        for i of translations
          html = '- ' + translations[i]
          if with_reference
            html += ' [' + data.ids[i] + '] ' + '<a href="javascript:addReference(' + data.ids[i] + ', ' + getSelectionStart() + ')">Add reference</a>'
          html += '<br>'
          $('#sidepanel').append html
    ).error ->
      displayError 'Ошибка получения перевода.'