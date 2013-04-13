show = (id) ->
    $('#translation' + id).show()
    $('#translationMask' + id).hide()

evaluate = (id, result) ->
  show id
  $.post(url_ajax_evaluate,
    id: id
    result: result
  , (data) ->
  ).error ->
    displayError 'Ошибка сохранения результата.'
