from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AgentChatView, AgentSkillsView, AsrView, ChatSessionViewSet

urlpatterns = [
    path('chat/', AgentChatView.as_view(), name='agent-chat'),
    path('skills/', AgentSkillsView.as_view(), name='agent-skills'),
    path('asr/', AsrView.as_view(), name='agent-asr'),
]

router = DefaultRouter()
router.register('sessions', ChatSessionViewSet, basename='chat-session')
urlpatterns += router.urls

