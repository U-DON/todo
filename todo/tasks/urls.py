from django.conf.urls import patterns, include, url

from . import views
from .api import TaskResource

task_resource = TaskResource()

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^', include(task_resource.urls)),
)
