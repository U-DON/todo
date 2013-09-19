from datetime import datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

import pytz
import redis
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource

from .models import Task
from .tasks import clean_tasks

class TaskResource(ModelResource):
    current = fields.BooleanField(default=False)
    done = fields.BooleanField(default=False)
    routine = fields.BooleanField(default=False)

    class Meta:
        always_return_data = True
        authorization = Authorization()
        queryset = Task.objects.all()
        resource_name = 'todo'

    def dehydrate_current(self, bundle):
        return bundle.obj.is_current()

    def dehydrate_done(self, bundle):
        return bundle.obj.is_done()

    def dehydrate_routine(self, bundle):
        return bundle.obj.is_routine

    def dehydrate(self, bundle):
        done_time = bundle.obj.epoch_done_time()
        if done_time is not None:
            bundle.data['doneTime'] = done_time
        return bundle

    def hydrate(self, bundle):
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        redis_pipeline = redis_client.pipeline()

        # Hack to avoid extraneous hydrate with invalid object.
        if bundle.obj.pk is None:
            return bundle

        if bundle.data['current']:
            redis_pipeline.sadd('todo:current', bundle.obj.pk)
        else:
            redis_pipeline.srem('todo:current', bundle.obj.pk)

        if bundle.data['done']:
            done_time = timezone.make_aware(datetime.utcnow(), timezone.utc)
            redis_pipeline.sadd('todo:done', bundle.obj.pk) \
                          .hset('todo#{task_id}'.format(task_id=bundle.obj.pk), 'done_time', done_time)
            local_timezone = pytz.timezone('America/New_York')
            local_datetime = timezone.utc.localize(datetime.utcnow()).astimezone(local_timezone)
            local_midnight = local_timezone.localize(datetime.combine(local_datetime.date() + timedelta(days=1), time()))
            midnight = local_midnight.astimezone(timezone.utc)
            clean_tasks.apply_async(eta=midnight)
        else:
            redis_pipeline.srem('todo:done', bundle.obj.pk) \
                          .delete('todo#{task_id}'.format(task_id=bundle.obj.pk), 'done_time')

        redis_pipeline.execute()

        return bundle

    def obj_delete(self, bundle, **kwargs):
        obj = self.obj_get(bundle, **kwargs)
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        redis_client.srem('todo:current', obj.pk)
        redis_client.srem('todo:done', obj.pk)
        redis_client.delete('todo#{task_id}'.format(task_id=obj.pk))
        super(TaskResource, self).obj_delete(bundle, **kwargs)
