from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.core.urlresolvers import NoReverseMatch

from tastypie import fields
from tastypie.authentication import SessionAuthentication
from tastypie.bundle import Bundle
from tastypie.resources import ModelResource, trailing_slash

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

    def get_object_list(self, request):
        if request.path == self.get_resource_uri(url_name='api_get_current_tasks'):
            return Task.objects.current()
        if request.path == self.get_resource_uri(url_name='api_get_later_tasks'):
            return Task.objects.later()
        if request.path == self.get_resource_uri(url_name='api_get_done_tasks'):
            return Task.objects.done()
        return super(TaskResource, self).get_object_list(request)

    def prepend_urls(self):
        return [
            url(r'^(?P<resource_name>%s)/now%s$' % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_list'), name='api_get_current_tasks'),
            url(r'^(?P<resource_name>%s)/later%s$' % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_list'), name='api_get_later_tasks'),
            url(r'^(?P<resource_name>%s)/done%s$' % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_list'), name='api_get_done_tasks'),
        ]

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
            return self._build_reverse_url('{url_name}'.format(url_name=url_name), kwargs=self.resource_uri_kwargs(bundle_or_obj))
        except NoReverseMatch:
            return ''

    def obj_delete(self, bundle, **kwargs):
        bundle.obj = self.obj_get(bundle=bundle, **kwargs)
        bundle.obj.set_current(False)
        bundle.obj.set_done(False)
        return super(TaskResource, self).obj_delete(bundle, **kwargs)

    def obj_update(self, bundle, skip_errors=False, **kwargs):
        bundle = super(TaskResource, self).obj_update(bundle, skip_errors, **kwargs)
        bundle.obj.set_current(bundle.data['current'])
        bundle.obj.set_done(bundle.data['done'])
        return bundle
