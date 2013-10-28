from .models import Profile

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView

from .forms import RegistrationForm

class RegistrationView(CreateView):
    model = get_user_model()
    form_class = RegistrationForm
    template_name = 'profiles/register.html'
    success_url = '/'
