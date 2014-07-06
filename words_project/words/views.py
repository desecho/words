# -*- coding: utf8 -*-
from django.http import HttpResponse
from django.shortcuts import redirect
from words.models import Word, Text, Reference, Language
from annoying.decorators import ajax_request, render_to
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
import hunspell

'''
knowledge levels:
0 - undetermined
1 - learned
2 - unlearned
3 - anki
'''

NUMBER_OF_WORDS_PER_LISTING = 50
HUNSPELL_PATH = '/usr/share/hunspell/'
HUNSPELL_NAME = {'fr': 'fr_CA', 'en': 'en_US'}


def addSynonyms(words):
    def filterDuplicatedSynonyms(words):
        synonyms = []
        words_output = []
        for word in words:
            synonym = word.synonyms
            if synonym not in synonyms or synonym == 0:
                synonyms.append(synonym)
                words_output.append(word)
        return words_output

    def addActualSynonyms(words):
        # def isRequiredToSkip(words):
        #     for word in words:
        #         if word.knowledge_level == 3:
        #             return True
        words_output = []
        for word in words:
            synonym = word.synonyms
            if synonym:
                word.synonyms = Word.objects.filter(synonyms=synonym)
                word.translation += ' (%s)' % len(word.synonyms)
                # skip_word = isRequiredToSkip(word.synonyms)
            else:
                word.synonyms = Word.objects.filter(id=word.id)
            # if not skip_word:
            words_output.append(word)
        return words_output
    words = filterDuplicatedSynonyms(words)
    words = addActualSynonyms(words)
    return words


def logout_view(request):
    logout(request)
    return redirect('/login/')


@render_to('home.html')
@login_required
def home(request, language):
    stats = {}
    words = Word.objects.filter(language__short_name=language)
    stats['total'] = len(words)
    stats['undetermined'] = len(words.filter(knowledge_level=0, language__short_name=language))
    stats['learned'] = (len(words.filter(knowledge_level=1)), len(words.filter(knowledge_level=1).exclude(date=None)))
    stats['unlearned'] = len(words.filter(knowledge_level=2))
    stats['anki'] = len(words.filter(knowledge_level=3))
    return {'stats': stats, 'language': language}


@render_to('index.html')
@login_required
def index(request):
    languages = Language.objects.all()
    return {'languages': languages}


@render_to('words.html')
@login_required
def words(request, language):
    words = Word.objects.filter(knowledge_level=0, language__short_name=language)
    words = words.filter(date=None)
    words = words.order_by('?')[:NUMBER_OF_WORDS_PER_LISTING]
    words = addSynonyms(words)
    return {'words': words}


def getProcessedText(id):
    text = Text.objects.get(id=id)
    text.text = text.text.replace(u'’', "'")  # replaces apostrophes
    return text


@render_to('texts.html')
@login_required
def texts(request, language):
    texts = Text.objects.filter(language__short_name=language)
    return {'texts': texts, 'language': language}


@render_to('text_edit.html')
@login_required
def text_edit(request, language, id):
    text = getProcessedText(id)
    return {'text': text, 'language': language}


@render_to('text.html')
@login_required
def text(request, language, id):
    def markText(text):
        def getReferenceLength(reference):
            if reference.length:
                return reference.length
            else:
                return len(reference.word.word)

        def getTextToReplace(text, position, shift, length):
            def fixToReplaceValue(to_replace, position, length, text):
                while to_replace.count("\n"):
                    position += to_replace.count("\n")
                    to_replace = text[position:position + length]
                return to_replace
            position += shift
            position += text[:position].count("\n")  # a hack to solve a strange problem with new lines
            to_replace = text[position:position + length]
            to_replace = fixToReplaceValue(to_replace, position, length, text)  # another hack to solve a strange problem with new lines
            return to_replace

        def getReplacementText(knowledge_level, translation, word_id, reference_id):
            def getColor(knowledge_level):
                if knowledge_level == 0:
                    color = 'grey'
                elif knowledge_level == 1:
                    color = 'green'
                elif knowledge_level == 2:
                    color = 'red'
                else:
                    color = 'blue'
                return color
            replacement = '<span class="highlight-%s" title="%s" id="reference%d">' % (getColor(knowledge_level), translation, reference_id) + to_replace + '</span>'
            if knowledge_level < 3:
                replacement += '<a href="javascript:evaluate(%d, 0, %d)">[-]</a>' % (word_id, reference_id)
                replacement += ' <a href="javascript:evaluate(%d, 1, %d)">[+]</a> ' % (word_id, reference_id)
            return replacement
        references = Reference.objects.filter(text=text).order_by('position')
        shift = 0
        for reference in references:
            length = getReferenceLength(reference)
            to_replace = getTextToReplace(text.text, reference.position, shift, length)
            replacement = getReplacementText(reference.word.knowledge_level, reference.word.translation, reference.word_id, reference.id)
            text.text = text.text.replace(to_replace, replacement, 1)
            shift += len(replacement) - length
        return text.text
    text = getProcessedText(id)
    text.text = markText(text)
    text.text = text.text.replace("\n", "<br>")
    return {'text': text, 'language': language}


def ajax_evaluate(request):
    def getKnowledgeLevel(result):
        if result:
            return 1
        else:
            return 2

    def updateKnowledgeLevel(id, knowledge_level):
        w = Word.objects.get(pk=id)
        w.knowledge_level = knowledge_level
        w.save()
    if request.is_ajax() and request.method == 'POST':
        POST = request.POST
        if 'id' in POST and 'result' in POST:
            id = int(POST.get('id'))
            result = int(POST.get('result'))
            updateKnowledgeLevel(id, getKnowledgeLevel(result))
    return HttpResponse()


@ajax_request
def ajax_get_translations(request):
    def generateListOfWords(word, language):
        def setHunspell(language):
            main_path = HUNSPELL_PATH + HUNSPELL_NAME[language]
            return hunspell.HunSpell(main_path + '.dic', main_path + '.aff')
        h = setHunspell(language)
        word_list = h.stem(word)
        if word not in word_list:
            word_list.append(word)
        return word_list

    def generateResponse(words):
        translations = []
        ids = []
        for w in words:
            translations.append(w.translation + ' (%s)' % w.part_of_speech)
            ids.append(w.id)
        return {'translations': translations, 'ids': ids}
    if request.is_ajax() and request.method == 'POST':
        POST = request.POST
        if 'word' in POST and 'language' in POST:
            word = POST.get('word')
            language = POST.get('language')
            word = word.encode('utf8')
            word_list = generateListOfWords(word, language)
            '''2DO: Needs work'''
            words = Word.objects.filter(word__in=word_list, language__short_name=language)
            if not len(words) and word[-1] == 's':
                words = Word.objects.filter(word=word[0:-1], language__short_name=language)
            response = generateResponse(words)
            return response


@ajax_request
def ajax_add_reference(request):
    def getLengthToRecord(word_id, length):
        if len(Word.objects.get(id=word_id).word) == length:
            return 0
        else:
            return length

    def createReference(word_id, text_id, position, length):
        r = Reference(word_id=word_id, text_id=text_id, position=position, length=length)
        r.save()
    if request.is_ajax() and request.method == 'POST':
        POST = request.POST
        if 'text_id' in POST and 'word_id' in POST and 'position' in POST and 'length' in POST:
            text_id = int(POST.get('text_id'))
            word_id = int(POST.get('word_id'))
            position = int(POST.get('position'))
            length = int(POST.get('length'))
            length = getLengthToRecord(word_id, length)
            createReference(word_id, text_id, position, length)
    return HttpResponse()


@render_to('anki.html')
@login_required
def anki(request, language):
    words = Word.objects.filter(knowledge_level=2, language__short_name=language)
    # from itertools import chain
    # result_list = list(chain(page_list, article_list, post_list))
    # words_without_synonyms = words.filter(synonyms=0)
    # words_with_synonyms = words.exclude(synonyms=0).distinct('synonyms')
    words = addSynonyms(words)
    return {'words': words}


@render_to('script.html')
@login_required
def set_anki(request, language):
    Word.objects.filter(knowledge_level=2, language__short_name=language).update(knowledge_level=3)
    return {'output': 'Done'}
