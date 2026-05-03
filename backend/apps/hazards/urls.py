from rest_framework.routers import DefaultRouter
from .views import HazardDetectionViewSet

router = DefaultRouter()
router.register('', HazardDetectionViewSet, basename='hazard-detection')
urlpatterns = router.urls
