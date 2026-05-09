"""URL Configuration."""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import FileResponse, HttpResponse
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import LoginView

def _spa_fallback(_request, _path=''):
    """生产环境直接访问 Gunicorn 时的 SPA fallback。"""
    index_path = settings.STATIC_ROOT / 'index.html'
    if index_path.exists():
        return FileResponse(open(index_path, 'rb'))
    return HttpResponse(
        'index.html not found. Please build frontend and run collectstatic.',
        status=404,
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/', include('apps.users.urls')),
    path('api/knowledge/', include('apps.knowledge.urls')),
    path('api/hazards/', include('apps.hazards.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/skill-permissions/', include('apps.skill_permissions.urls')),
    path('api/agent/', include('apps.agent.urls')),
    path('api/labs/', include('apps.labs.urls')),
    path('api/scenarios/', include('apps.scenarios.urls')),
    # SPA fallback：非 API / static / media 请求返回前端 index.html
    re_path(r'^(?!static/|media/|api/|admin/).*$', _spa_fallback),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # 生产环境由 Django 直接 serve media（推荐通过 Nginx 代理以获得更好性能）
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
