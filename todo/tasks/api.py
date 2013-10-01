from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.bundle import Bundle
from tastypie.resources import ModelResource

from .models import Task

class TaskResource(ModelResource):
    current = fields.BooleanField(default=False)
    done = fields.BooleanField(default=False)
    routine = fields.BooleanField(default=False)

    class Meta:
        always_return_data = True
        authorization = Authorization()
        fields = ['id', 'title']
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

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if bundle_or_obj is not None:
            url_name = 'api_dispatch_detail'
        try:
            return self._build_reverse_url('tasks:{url_name}'.format(url_name=url_name), kwargs=self.resource_uri_kwargs(bundle_or_obj))
        except NoReverseMatch:
            return ''

    def obj_delete(self, bundle, **kwargs):
        obj = self.obj_get(bundle, **kwargs)
        obj.set_current(False)
        obj.set_done(False)
        return super(TaskResource, self).obj_delete(bundle, **kwargs)

    def obj_update(self, bundle, skip_errors=False, **kwargs):
        obj = self.obj_get(bundle, **kwargs)
        obj.set_current(bundle.data['current'])
        obj.set_done(bundle.data['done'])
        return super(TaskResource, self).obj_update(bundle, skip_errors, **kwargs)
