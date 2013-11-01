from django.contrib.auth import get_user_model
from django.core.urlresolvers import NoReverseMatch

from tastypie import fields
from tastypie.authentication import SessionAuthentication
from tastypie.bundle import Bundle
from tastypie.resources import ModelResource

from profiles.api import UserAuthorization, UserResource

from .models import Task

class TaskResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')
    current = fields.BooleanField(default=False)
    done = fields.BooleanField(default=False)
    routine = fields.BooleanField(default=False)

    class Meta:
        always_return_data = True
        authentication = SessionAuthentication()
        authorization = UserAuthorization()
        fields = ['id', 'title']
        queryset = Task.objects.all()
        resource_name = 'todo'

    def dehydrate_user(self, bundle):
        return bundle.obj.user

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

    def hydrate_user(self, bundle):
        bundle.data['user'] = get_user_model().objects.get(pk=bundle.request.user.pk)
        return bundle

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if bundle_or_obj is not None:
            url_name = 'api_dispatch_detail'
        try:
            return self._build_reverse_url('tasks:{url_name}'.format(url_name=url_name), kwargs=self.resource_uri_kwargs(bundle_or_obj))
        except NoReverseMatch:
            return ''

    def obj_delete(self, bundle, **kwargs):
        bundle = super(TaskResource, self).obj_delete(bundle, **kwargs)
        bundle.obj.set_current(False)
        bundle.obj.set_done(False)
        return bundle

    def obj_update(self, bundle, skip_errors=False, **kwargs):
        bundle = super(TaskResource, self).obj_update(bundle, skip_errors, **kwargs)
        bundle.obj.set_current(bundle.data['current'])
        bundle.obj.set_done(bundle.data['done'])
        return bundle
