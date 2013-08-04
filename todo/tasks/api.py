from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from .models import Task

class TaskResource(ModelResource):
    class Meta:
        always_return_data = True
        authorization = Authorization()
        queryset = Task.objects.all()
        resource_name = 'todo'
