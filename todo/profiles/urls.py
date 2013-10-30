from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse_lazy

from . import views

urlpatterns = patterns('',
    url(r'^register/$', views.RegistrationView.as_view(), name='register'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'profiles/login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': reverse_lazy('profiles:login')}, name='logout'),
    url(r'^password_change/$', 'django.contrib.auth.views.password_change', {'template_name': 'profiles/password_change.html', 'post_change_redirect': reverse_lazy('profiles:password_change_done')}, name='password_change'),
    url(r'^password_change/done/$', views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    url(r'^password_reset/$', 'django.contrib.auth.views.password_reset', {'template_name': 'profiles/password_reset.html', 'email_template_name': 'profiles/password_reset_email.html', 'subject_template_name': 'profiles/password_reset_subject.txt', 'post_reset_redirect': reverse_lazy('profiles:password_reset_done')}, name='password_reset'),
    url(r'^password_reset/done/$', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    url(r'^password_reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 'django.contrib.auth.views.password_reset_confirm', {'template_name': 'profiles/password_reset_confirm.html', 'post_reset_redirect': reverse_lazy('profiles:password_change_done')}, name='password_reset_confirm'),
)
