from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import FireScenarioViewSet, TrainingMaterialViewSet

router = DefaultRouter()
router.register(r'materials', TrainingMaterialViewSet, basename='material')
router.register(r'', FireScenarioViewSet, basename='scenario')

urlpatterns = [
    path('', include(router.urls)),
]
