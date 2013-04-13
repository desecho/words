evaluate = (word_id, result, reference_id) ->
    $.post(url_ajax_evaluate, {id: word_id, result: result},
      (data) ->
        if result is 1
          color = 'green'
        else
          color = 'red'
        $('#reference' + reference_id).attr('class', 'highlight-' + color)
    ).error ->
      displayError 'Ошибка сохранения результата.'

$ ->
  $('#text').mouseup(
    ->
      $('#sidepanel').empty()
      word = window.getSelection().toString()
      get_translations(word)
  )