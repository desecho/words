from words.models import Word, Text
from django.contrib import admin


class WordAdmin(admin.ModelAdmin):
    search_fields = ['word']
    list_filter = ['part_of_speech']

admin.site.register(Word, WordAdmin)
admin.site.register(Text)
