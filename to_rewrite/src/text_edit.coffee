getSelectionStart = -> $('#text')[0].selectionStart

getSelectionLength = -> getSelectedWord().length

showPosition = ->
  position_length = getSelectionStart() + ', ' + getSelectionLength()
  html = """ #{ position_length } <a href="javascript:addManualReference(#{ position_length })">Add reference</a> """
  $('#status').html html

getSelectionEnd = -> $('#text')[0].selectionEnd

getSelectedWord = ->
  # Trim to correctly count the length
  $('#text').val().substring(getSelectionStart(), getSelectionEnd()).trim()

$ ->
  $('#text').click ->
    $('#sidepanel').empty()
    showPosition()
    word = getSelectedWord()
    get_translations word, true

  $('#text').keyup ->
    showPosition()

addManualReference = (position, length) ->
  word_id = $('#word_id').val()
  if word_id
    addReference word_id, position, length

addReference = (word_id, position, length = getSelectionLength()) ->
  #length = (if typeof length isnt 'undefined' then length else getSelectionLength())
  $.post('/add_reference/',
    text_id: text_id
    word_id: word_id
    position: position
    length: length
  , (data) ->
    $('#word_id').val ''
  ).error ->
    displayError 'Ошибка добавления ссылки.'
