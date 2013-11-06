from django import forms
from django.contrib.auth import get_user_model

import pytz

from .models import Profile

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    timezone = forms.ChoiceField(initial='', choices=[(tz, tz) for tz in pytz.common_timezones])

    class Meta:
        model = get_user_model()
        fields = ('email', 'name', 'password')

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            profile = Profile(user=user, timezone=self.cleaned_data['timezone'])
            profile.save()
        return user
