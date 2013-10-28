from django.conf.urls import patterns, include, url

from . import views

urlpatterns = patterns('',
    url('^register/', views.RegistrationView.as_view()),
    url('^accounts/', include('django.contrib.auth.urls')),
)
