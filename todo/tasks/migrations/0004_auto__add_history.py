# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'History'
        db.create_table(u'tasks_history', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(related_name='history', to=orm['tasks.Task'])),
            ('done_time', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'tasks', ['History'])


    def backwards(self, orm):
        # Deleting model 'History'
        db.delete_table(u'tasks_history')


    models = {
        u'tasks.history': {
            'Meta': {'object_name': 'History'},
            'done_time': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'history'", 'to': u"orm['tasks.Task']"})
        },
        u'tasks.task': {
            'Meta': {'object_name': 'Task'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_routine': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['tasks']