from datetime import datetime

from django.conf import settings
from django.utils import timezone

import redis
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource

from .models import Task

class TaskResource(ModelResource):
    current = fields.BooleanField(default=False)
    done = fields.BooleanField(default=False)
    done_time = fields.DateTimeField()

    class Meta:
        always_return_data = True
        authorization = Authorization()
        queryset = Task.objects.all()
        resource_name = 'todo'

    def dehydrate_current(self, bundle):
        return bundle.obj.is_current()

    def dehydrate_done(self, bundle):
        return bundle.obj.is_done()

    def dehydrate_done_time(self, bundle):
        return bundle.obj.epoch_done_time()

    def hydrate_current(self, bundle):
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        if bundle.data['current']:
            redis_client.sadd('todo:current', bundle.obj.pk)
        else:
            redis_client.srem('todo:current', bundle.obj.pk)
        return bundle

    def hydrate_done(self, bundle):
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        redis_pipeline = redis_client.pipeline()
        if bundle.data['done']:
            done_time = timezone.make_aware(datetime.utcnow(), timezone.utc)
            redis_pipeline.sadd('todo:done', bundle.obj.pk)
            redis_pipeline.hset('todo#{task_id}'.format(task_id=bundle.obj.pk), 'done_time', done_time)
            redis_pipeline.execute()
        else:
            redis_pipeline.srem('todo:done', bundle.obj.pk)
            redis_pipeline.hdel('todo#{task_id}'.format(task_id=bundle.obj.pk), 'done_time')
            redis_pipeline.execute()
        return bundle
