from django.db import models
from django.contrib.auth.models import AbstractUser

class Language(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=2)

    def __unicode__(self):
        return self.name


class Theme(models.Model):
    parent = models.ForeignKey('self', models.CASCADE, blank=True, null=True,
                               related_name='child')
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Word(models.Model):
    language = models.ForeignKey(Language, models.CASCADE)
    theme = models.ForeignKey(Theme, models.SET_NULL, null=True, blank=True)
    word = models.CharField(max_length=255)
    translation = models.CharField(max_length=255)
    definition = models.CharField(max_length=255, null=True, blank=True)
    transcription = models.CharField(max_length=255, null=True, blank=True)
    synonyms = models.IntegerField(default=0)
    part_of_speech = models.CharField(max_length=10)
    preposition = models.CharField(max_length=10)
    gender = models.IntegerField(default=0, null=True, blank=True)
    gender_rule = models.IntegerField(default=0)
    level = models.IntegerField(default=0)
    date = models.DateField(auto_now=True, null=True)
    export_to_anki = models.BooleanField(default=False)
    exported_to_anki = models.BooleanField(default=False)
    known = models.BooleanField(default=False)
    example = models.CharField(max_length=255, null=True, blank=True)

    @property
    def word_display(self):
        if self.gender is not None:
            if self.gender == 0:
                gender = 'f'
            elif self.gender == 1:
                gender = 'm'
            else:
                gender = '-'
            gender = f' ({gender}) '
        else:
            gender = ''
        if self.transcription:
            transcription = f' [{self.transcription}]'
        else:
            transcription = ''
        if self.preposition:
            preposition = ' ' + self.preposition
        else:
            preposition = ''
        if self.gender_rule:
            gender_rule = ' (gender exception)'
        else:
            gender_rule = ''
        if self.example:
            example = ' ' + self.example
        else:
            example = ''
        return self.word + preposition + gender + transcription + f' ({self.part_of_speech})' + gender_rule + example

    @property
    def translation_display(self):
        if self.definition:
            definition = ' ' + self.definition
        else:
            definition = ''
        return self.translation + definition

    def __unicode__(self):
        return self.word


class Text(models.Model):
    name = models.CharField(max_length=255)
    text = models.TextField()
    url = models.URLField(null=True, blank=True)
    language = models.ForeignKey(Language, models.CASCADE)

    def __unicode__(self):
        return self.name


class Reference(models.Model):
    word = models.ForeignKey(Word, models.CASCADE)
    text = models.ForeignKey(Text, models.CASCADE)
    position = models.IntegerField()
    length = models.IntegerField(default=0)

    def __unicode__(self):
        return self.word


class User(AbstractUser):
    pass
