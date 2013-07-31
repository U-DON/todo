from django.conf.urls import patterns, include, url

from tasks.api import TaskResource

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

task_resource = TaskResource()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'todo.views.home', name='home'),
    # url(r'^todo/', include('todo.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('tasks.urls', namespace='tasks')),
    url(r'^', include(task_resource.urls, namespace='tasks_api')),
)
