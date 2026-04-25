from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import HttpResponse
import os


def favicon(request):
    return HttpResponse(status=204)


def serve_frontend(request, filename):
    from django.http import FileResponse, Http404
    file_path = os.path.join(
        settings.BASE_DIR, 'static', 'frontend', filename
    )
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    raise Http404


def serve_frontend_asset(request, folder, filename):
    from django.http import FileResponse, Http404
    file_path = os.path.join(
        settings.BASE_DIR, 'static', 'frontend', folder, filename
    )
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    raise Http404


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/qa/', include('qa_engine.urls')),
    path('favicon.ico', favicon),

    # Serve frontend pages
    path('', RedirectView.as_view(url='/login')),
    path('login', serve_frontend, {'filename': 'login.html'}),
    path('register', serve_frontend, {'filename': 'register.html'}),
    path('app', serve_frontend, {'filename': 'index.html'}),

    # Serve CSS and JS
    path('css/<str:filename>', serve_frontend_asset, {'folder': 'css'}),
    path('js/<str:filename>', serve_frontend_asset, {'folder': 'js'}),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)