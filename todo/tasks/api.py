from django.conf import settings

import redis
from restless.dj import DjangoResource
from restless.preparers import FieldsPreparer

from .models import Task

class TaskResource(DjangoResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'title': 'title',
        'repeatable': 'is_repeatable'
    })

    def prepare(self, data):
        prepped = super(TaskResource, self).prepare(data)
        # Check 'current' and 'done' by querying Redis.
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        prepped['current'] = redis_client.sismember('todo:current', prepped['id'])
        prepped['done'] = redis_client.sismember('todo:done', prepped['id'])
        return prepped

    def is_authenticated(self):
        return True
        # return self.request.user.is_authenticated()

    def list(self):
        return Task.objects.all()

    def detail(self, pk):
        return Task.objects.get(id=pk)
