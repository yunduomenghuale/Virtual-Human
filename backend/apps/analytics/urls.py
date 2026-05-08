from django.urls import path
from .views import DashboardView, LabsView, RootCauseAnalysisView, RiskPredictionView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='analytics-dashboard'),
    path('labs/', LabsView.as_view(), name='analytics-labs'),
    path('root-cause/', RootCauseAnalysisView.as_view(), name='analytics-root-cause'),
    path('prediction/', RiskPredictionView.as_view(), name='analytics-prediction'),
]
