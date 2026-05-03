from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import KnowledgeQAView, KnowledgeQAStreamView, QASessionViewSet, KnowledgeDocumentViewSet

router = DefaultRouter()
router.register('documents', KnowledgeDocumentViewSet, basename='kb-doc')
router.register('sessions', QASessionViewSet, basename='qa-session')

urlpatterns = [
    path('ask/', KnowledgeQAView.as_view(), name='kb-ask'),
    path('ask/stream/', KnowledgeQAStreamView.as_view(), name='kb-ask-stream'),
] + router.urls
