from django.conf.urls import patterns, include, url

from . import views
from .api import TaskResource

task_resource = TaskResource()

urlpatterns = patterns('',
    url(r'^$', views.TaskIndexView.as_view(), name='index'),
)
