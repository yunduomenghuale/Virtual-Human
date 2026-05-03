from django.urls import path
from .views import DashboardView, LabsView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='analytics-dashboard'),
    path('labs/', LabsView.as_view(), name='analytics-labs'),
]
