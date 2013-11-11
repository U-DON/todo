from django.views.generic import ListView

from .models import Task
from profiles.views import CacheControlMixin, LoginRequiredMixin

class TaskIndexView(CacheControlMixin, LoginRequiredMixin, ListView):
    context_object_list = 'tasks'
    template_name = 'tasks/index.html'

    def get_queryset(self):
        return Task.objects.current()
