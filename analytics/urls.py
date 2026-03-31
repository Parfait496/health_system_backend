from django.urls import path
from .views import (
    DiseaseReportCreateView,
    DiseaseReportListView,
    OutbreakAlertView,
    DashboardSummaryView,
    RegionalInsightView,
    HealthMetricListView,
)

urlpatterns = [
    path('disease-reports/',            DiseaseReportCreateView.as_view(), name='disease-report-create'),
    path('disease-reports/all/',        DiseaseReportListView.as_view(),   name='disease-report-list'),
    path('outbreaks/',                  OutbreakAlertView.as_view(),       name='outbreak-alerts'),
    path('dashboard/',                  DashboardSummaryView.as_view(),    name='dashboard'),
    path('regional/<str:district>/',    RegionalInsightView.as_view(),     name='regional-insight'),
    path('metrics/',                    HealthMetricListView.as_view(),    name='health-metrics'),
]