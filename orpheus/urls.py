"""orpheus URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from policies.admin import admin_site
from django.views.generic import RedirectView
from rest_framework.documentation import include_docs_urls

from orpheus import views

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/policies/', permanent=True)),
    url(r'^policies/', include('policies.urls', namespace='policies')),
    url(r'^admin/', admin_site.urls),
]

#Add Django site authentication urls (for login, logout, password management)
urlpatterns += [
    url(r'^accounts/', include('django.contrib.auth.urls')),
]

# RESTful API
urlpatterns += [
    url(r'^api/', views.api_root),
    url(r'^api_docs/', include_docs_urls(title='Orpheus API', description='RESTful API for Orpheus')),
]

# Django-select2
urlpatterns += [
    url(r'^select2/', include('django_select2.urls')),
]