from django.views.generic import ListView

from .models import Task
from profiles.views import CacheControlMixin, LoginRequiredMixin

class TaskIndexView(LoginRequiredMixin, CacheControlMixin, ListView):
    model = Task
    queryset = Task.objects.current()
    template_name = 'tasks/index.html'
