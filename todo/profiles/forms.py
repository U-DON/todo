from django import forms
from django.contrib.auth import get_user_model

from .models import Profile

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'name', 'password')
