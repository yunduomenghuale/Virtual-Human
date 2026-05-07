"""URL Configuration."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import LoginView

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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
