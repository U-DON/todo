from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.generic.base import View
from django.views.generic.edit import CreateView

from .forms import RegistrationForm
from .models import Profile

class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

class CacheControlMixin(object):
    @method_decorator(cache_control(must_revalidate=True, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super(CacheControlMixin, self).dispatch(request, *args, **kwargs)

class RegistrationView(CreateView):
    model = get_user_model()
    form_class = RegistrationForm
    template_name = 'profiles/register.html'
    success_url = reverse_lazy('tasks:index')

class PasswordChangeDoneView(View):
    def get(self, request, *args, **kwargs):
        messages.success(request, "Password successfully changed.")
        return HttpResponseRedirect(reverse('tasks:index'))

class PasswordResetDoneView(View):
    def get(self, request, *args, **kwargs):
        messages.success(request, "Password has been reset. Check your email for further steps.")
        return HttpResponseRedirect(reverse('profiles:login'))
