from rest_framework.routers import DefaultRouter
from .views import SkillPermissionViewSet

router = DefaultRouter()
router.register('', SkillPermissionViewSet, basename='skill-permission')
urlpatterns = router.urls
