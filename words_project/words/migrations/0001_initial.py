# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Language'
        db.create_table(u'words_language', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=2)),
        ))
        db.send_create_signal(u'words', ['Language'])

        # Adding model 'Theme'
        db.create_table(u'words_theme', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='child', null=True, to=orm['words.Theme'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'words', ['Theme'])

        # Adding model 'Word'
        db.create_table(u'words_word', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['words.Language'])),
            ('theme', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['words.Theme'])),
            ('word', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('translation', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('transcription', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('synonyms', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('part_of_speech', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('preposition', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('gender', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('gender_rule', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('level', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('knowledge_level', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('date', self.gf('django.db.models.fields.DateField')(auto_now=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'words', ['Word'])

        # Adding model 'Text'
        db.create_table(u'words_text', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['words.Language'])),
        ))
        db.send_create_signal(u'words', ['Text'])

        # Adding model 'Reference'
        db.create_table(u'words_reference', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('word', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['words.Word'])),
            ('text', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['words.Text'])),
            ('position', self.gf('django.db.models.fields.IntegerField')()),
            ('length', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'words', ['Reference'])


    def backwards(self, orm):
        # Deleting model 'Language'
        db.delete_table(u'words_language')

        # Deleting model 'Theme'
        db.delete_table(u'words_theme')

        # Deleting model 'Word'
        db.delete_table(u'words_word')

        # Deleting model 'Text'
        db.delete_table(u'words_text')

        # Deleting model 'Reference'
        db.delete_table(u'words_reference')


    models = {
        u'words.language': {
            'Meta': {'object_name': 'Language'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        u'words.reference': {
            'Meta': {'object_name': 'Reference'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['words.Text']"}),
            'word': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['words.Word']"})
        },
        u'words.text': {
            'Meta': {'object_name': 'Text'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['words.Language']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'words.theme': {
            'Meta': {'object_name': 'Theme'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child'", 'null': 'True', 'to': u"orm['words.Theme']"})
        },
        u'words.word': {
            'Meta': {'object_name': 'Word'},
            'date': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'gender_rule': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'knowledge_level': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['words.Language']"}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'part_of_speech': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'preposition': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'synonyms': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'theme': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['words.Theme']"}),
            'transcription': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'translation': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'word': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['words']