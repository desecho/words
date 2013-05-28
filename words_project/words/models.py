from django.db import models


class Language(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=2)

    def __unicode__(self):
        return self.name


class Theme(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, related_name='child')
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Word(models.Model):
    language = models.ForeignKey(Language)
    theme = models.ForeignKey(Theme)
    word = models.CharField(max_length=255)
    translation = models.CharField(max_length=255)
    transcription = models.CharField(max_length=255, null=True, blank=True)
    synonyms = models.IntegerField(default=0)
    part_of_speech = models.CharField(max_length=10)
    preposition = models.CharField(max_length=10)
    gender = models.IntegerField(default=0, null=True, blank=True)
    gender_rule = models.IntegerField(default=0)
    level = models.IntegerField(default=0)
    knowledge_level = models.IntegerField(default=0)

    def word_display(self):
        if self.gender is not None:
            if self.gender == 0:
                gender = 'f'
            elif self.gender == 1:
                gender = 'm'
            else:
                gender = '-'
            gender = ' (%s) ' % gender
        else:
            gender = ''
        if self.transcription:
            transcription = ' [%s]' % self.transcription
        else:
            transcription = ''
        if self.preposition:
            preposition = ' ' + self.preposition
        else:
            preposition = ''
        return self.word + preposition + gender + transcription

    def __unicode__(self):
        return self.word


class Text(models.Model):
    name = models.CharField(max_length=255)
    text = models.TextField()
    url = models.URLField(null=True, blank=True)
    language = models.ForeignKey(Language)

    def __unicode__(self):
        return self.name


class Reference(models.Model):
    word = models.ForeignKey(Word)
    text = models.ForeignKey(Text)
    position = models.IntegerField()
    length = models.IntegerField(default=0)

    def __unicode__(self):
        return self.word
