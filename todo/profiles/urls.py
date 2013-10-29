from django.conf.urls import patterns, include, url

from . import views

urlpatterns = patterns('',
    url(r'^register/$', views.RegistrationView.as_view(), name='register'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'profiles/login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/login/'}, name='logout')
)
