from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required

from . import views
from .api import TaskResource

task_resource = TaskResource()

urlpatterns = patterns('',
    url(r'^$', login_required(views.IndexView.as_view()), name='index'),
)
