from django.conf import settings

import redis
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from .models import Task

class TaskResource(ModelResource):
    active = fields.BooleanField(default=False)
    done = fields.BooleanField(default=False)

    class Meta:
        always_return_data = True
        authorization = Authorization()
        queryset = Task.objects.all()
        resource_name = 'todo'

    def dehydrate_active(self, bundle):
        return bundle.obj.active()

    def dehydrate_done(self, bundle):
        return bundle.obj.done()

    def hydrate_active(self, bundle):
        r = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        if bundle.data['active']:
            r.sadd('active', bundle.obj.pk)
        else:
            r.srem('active', bundle.obj.pk)
        return bundle

    def hydrate_done(self, bundle):
        r = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        if bundle.data['done']:
            r.sadd('done', bundle.obj.pk)
        else:
            r.srem('done', bundle.obj.pk)
        return bundle
