from django.views import generic

from .models import Task

class IndexView(generic.ListView):
    model = Task
    template_name = 'tasks/index.html'
