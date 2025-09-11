"""
URL configuration for BTest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

from BTest import settings
from Bapp.error_views import ErrorHandlerView
from Bapp.users_views import home_page
from Bapp.views import index

# Définition des handlers
handler403 = ErrorHandlerView.handler403
handler404 = ErrorHandlerView.handler404
handler500 = ErrorHandlerView.handler500



urlpatterns = [
    path('', home_page, name='home'),
    path('admin/', admin.site.urls),
    path('', include('Caroussel.urls', namespace='Caroussel')),
    path('Bourou/', include('Bapp.urls', namespace='Bapp')),
    # Ajout explicite de l'URL pour servir les médias
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT,}),

]
