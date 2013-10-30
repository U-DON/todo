from django.conf.urls import patterns, include, url

from tastypie.api import Api

from profiles.api import UserResource
from tasks.api import TaskResource

api = Api(api_name='api')
api.register(UserResource())
api.register(TaskResource())

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'todo.views.home', name='home'),
    # url(r'^todo/', include('todo.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('tasks.urls', namespace='tasks')),
    url(r'^', include('profiles.urls', namespace='profiles')),
    url(r'^', include(api.urls)),
)
