# -*- coding: utf8 -*-
from .mixins import TemplateView, AjaxView
from django.http import HttpResponse
from django.shortcuts import redirect
from wordsapp.models import Word, Text, Reference, Language
from annoying.decorators import ajax_request, render_to
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
import hunspell
import io
import csv


NUMBER_OF_WORDS_PER_LISTING = 25
HUNSPELL_PATH = '/usr/share/hunspell/'
HUNSPELL_NAME = {'fr': 'fr_CA', 'en': 'en_US'}


class AnkiExportView(TemplateView):
    template_name = 'anki_export.html'
    content_type = 'application/text; charset=utf-8'

    def get_context_data(self, language):
        words = Word.objects.filter(export_to_anki=True,
                                    language__short_name=language)
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

        for word in words:
            # I don't know why we need strip() here but on one occasion a new line was introduced and I couldn't find where it came from.
            row = [word.word_display.strip(), word.translation_display.strip()]
            writer.writerow(row)
        return {'csv': output.getvalue()}


class LanguageView(TemplateView):
    template_name = 'language.html'

    def get_context_data(self, language):
        words = Word.objects.filter(language__short_name=language)
        stats = {'total': len(words)}
        return {'stats': stats, 'language': language}


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self):
        languages = Language.objects.all()
        return {'languages': languages}


class WordsView(TemplateView):
    template_name = 'words.html'

    def get_context_data(self, language):
        words = Word.objects.filter(exported_to_anki=False, export_to_anki=False, known=False,
                                    language__short_name=language)
        words = words[:NUMBER_OF_WORDS_PER_LISTING]
        return {'words': words}


class ExportToAnkiView(AjaxView):
    def put(self, request, **kwargs):
        word_id = kwargs['id']
        word = Word.objects.get(pk=word_id)
        word.export_to_anki = True
        word.save()
        return self.success()


class MarkAsKnownView(AjaxView):
    def put(self, request, **kwargs):
        word_id = kwargs['id']
        word = Word.objects.get(pk=word_id)
        word.known = True
        word.save()
        return self.success()


class MarkWordsAsExportedToAnkiView(AjaxView):
    def put(self, request, **kwargs):
        language = kwargs['language']
        word = Word.objects.filter(language__short_name=language, export_to_anki=True).update(exported_to_anki=True, export_to_anki=False)
        return self.success()

# def getProcessedText(id):
#     text = Text.objects.get(id=id)
#     text.text = text.text.replace(u'’', "'")  # replaces apostrophes
#     return text


# @render_to('texts.html')
# @login_required
# def texts(request, language):
#     texts = Text.objects.filter(language__short_name=language)
#     return {'texts': texts, 'language': language}


# @render_to('text_edit.html')
# @login_required
# def text_edit(request, language, id):
#     text = getProcessedText(id)
#     return {'text': text, 'language': language}


# @render_to('text.html')
# @login_required
# def text(request, language, id):
#     def markText(text):
#         def getReferenceLength(reference):
#             if reference.length:
#                 return reference.length
#             else:
#                 return len(reference.word.word)

#         def getTextToReplace(text, position, shift, length):
#             def fixToReplaceValue(to_replace, position, length, text):
#                 while to_replace.count('\n'):
#                     position += to_replace.count('\n')
#                     to_replace = text[position:position + length]
#                 return to_replace
#             position += shift
#             # a hack to solve a strange problem with new lines
#             position += text[:position].count('\n')
#             to_replace = text[position:position + length]
#             # another hack to solve a strange problem with new lines
#             to_replace = fixToReplaceValue(to_replace, position, length, text)
#             return to_replace

#         def getReplacementText(knowledge_level, translation, word_id,
#                                reference_id):
#             def getColor(knowledge_level):
#                 if knowledge_level == 0:
#                     color = 'grey'
#                 elif knowledge_level == 1:
#                     color = 'green'
#                 elif knowledge_level == 2:
#                     color = 'red'
#                 else:
#                     color = 'blue'
#                 return color
#             replacement = '<span class="highlight-%s" title="%s" id="reference%d">' % (getColor(knowledge_level), translation, reference_id) + to_replace + '</span>'
#             if knowledge_level < 3:
#                 replacement += '<a href="javascript:evaluate(%d, 0, %d)">[-]</a>' % (word_id, reference_id)
#                 replacement += ' <a href="javascript:evaluate(%d, 1, %d)">[+]</a> ' % (word_id, reference_id)
#             return replacement
#         references = Reference.objects.filter(text=text).order_by('position')
#         shift = 0
#         for reference in references:
#             length = getReferenceLength(reference)
#             to_replace = getTextToReplace(text.text, reference.position, shift,
#                                           length)
#             replacement = getReplacementText(reference.word.knowledge_level,
#                                              reference.word.translation,
#                                              reference.word_id, reference.id)
#             text.text = text.text.replace(to_replace, replacement, 1)
#             shift += len(replacement) - length
#         return text.text
#     text = getProcessedText(id)
#     text.text = markText(text)
#     text.text = text.text.replace('\n', '<br>')
#     return {'text': text, 'language': language}


# @ajax_request
# def ajax_get_translations(request):
#     def generateListOfWords(word, language):
#         def setHunspell(language):
#             main_path = HUNSPELL_PATH + HUNSPELL_NAME[language]
#             return hunspell.HunSpell(main_path + '.dic', main_path + '.aff')
#         h = setHunspell(language)
#         word_list = h.stem(word)
#         if word not in word_list:
#             word_list.append(word)
#         return word_list

#     def generateResponse(words):
#         translations = []
#         ids = []
#         for w in words:
#             translations.append(w.translation + ' (%s)' % w.part_of_speech)
#             ids.append(w.id)
#         return {'translations': translations, 'ids': ids}
#     if request.is_ajax() and request.method == 'POST':
#         POST = request.POST
#         if 'word' in POST and 'language' in POST:
#             word = POST.get('word')
#             language = POST.get('language')
#             word = word.encode('utf8')
#             word_list = generateListOfWords(word, language)
#             '''2DO: Needs work'''
#             words = Word.objects.filter(word__in=word_list,
#                                         language__short_name=language)
#             if not len(words) and word[-1] == 's':
#                 words = Word.objects.filter(word=word[0:-1],
#                                             language__short_name=language)
#             response = generateResponse(words)
#             return response


# @ajax_request
# def ajax_add_reference(request):
#     def getLengthToRecord(word_id, length):
#         if len(Word.objects.get(id=word_id).word) == length:
#             return 0
#         else:
#             return length

#     def createReference(word_id, text_id, position, length):
#         r = Reference(word_id=word_id, text_id=text_id, position=position,
#                       length=length)
#         r.save()
#     if request.is_ajax() and request.method == 'POST':
#         POST = request.POST
#         if ('text_id' in POST and 'word_id' in POST and 'position' in POST and
#                 'length' in POST):
#             text_id = int(POST.get('text_id'))
#             word_id = int(POST.get('word_id'))
#             position = int(POST.get('position'))
#             length = int(POST.get('length'))
#             length = getLengthToRecord(word_id, length)
#             createReference(word_id, text_id, position, length)
#     return HttpResponse()



# def addSynonyms(words):
#     def filterDuplicatedSynonyms(words):
#         synonyms = []
#         words_output = []
#         for word in words:
#             synonym = word.synonyms
#             if synonym not in synonyms or synonym == 0:
#                 synonyms.append(synonym)
#                 words_output.append(word)
#         return words_output

#     def addActualSynonyms(words):
#         # def isRequiredToSkip(words):
#         #     for word in words:
#         #         if word.knowledge_level == 3:
#         #             return True
#         words_output = []
#         for word in words:
#             synonym = word.synonyms
#             if synonym:
#                 word.synonyms = Word.objects.filter(synonyms=synonym)
#                 word.translation += ' (%s)' % len(word.synonyms)
#                 # skip_word = isRequiredToSkip(word.synonyms)
#             else:
#                 word.synonyms = Word.objects.filter(id=word.id)
#             # if not skip_word:
#             words_output.append(word)
#         return words_output
#     words = filterDuplicatedSynonyms(words)
#     words = addActualSynonyms(words)
#     return words



# @render_to('anki_export.html')
# @login_required
# def anki_export(request, language):
#     words = Word.objects.filter(export_to_anki=True,
#                                 language__short_name=language)
#     # from itertools import chain
#     # result_list = list(chain(page_list, article_list, post_list))
#     # words_without_synonyms = words.filter(synonyms=0)
#     # words_with_synonyms = words.exclude(synonyms=0).distinct('synonyms')
#     # words = addSynonyms(words)
#     return {'words': words}
