"""
URL configuration for deiva_gestion project.

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
import re as _re
from pathlib import Path
from mimetypes import guess_type as _guess_type

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import Http404, HttpResponse
from django.urls import path, re_path, include
from django.views.generic import RedirectView
from gestion_depot.forms import LoginForm


@login_required
def protected_media(request, path):
    media_root = Path(settings.MEDIA_ROOT).resolve()
    full_path = (media_root / path).resolve()
    if not full_path.is_relative_to(media_root) or not full_path.is_file():
        raise Http404
    ct = _guess_type(full_path.name)
    content_type = ct[0] if ct and ct[0] else 'application/octet-stream'
    safe_name = _re.sub(r'[^\w\-. ]', '_', full_path.name)
    with open(full_path, 'rb') as f:
        resp = HttpResponse(f.read(), content_type=content_type)
        resp['Content-Disposition'] = f'inline; filename="{safe_name}"'
        return resp


urlpatterns = [
    path('', RedirectView.as_view(url='/gestion/', permanent=False)),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=LoginForm,
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login'), name='logout'),
    path('gestion/', include('gestion_depot.urls')),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', protected_media),
]


