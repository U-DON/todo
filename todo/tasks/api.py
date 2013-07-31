from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from .models import Task

class TaskResource(ModelResource):
    class Meta:
        queryset = Task.objects.all()
        resource_name = 'todo'
        authorization = Authorization()
