from django.urls import path
from .views import (
    HospitalListView,
    HospitalCreateView,
    HospitalDetailView,
    NearestHospitalView,
    EmergencyRequestCreateView,
    EmergencyRequestListView,
    EmergencyStatusUpdateView,
    ActiveEmergenciesView,
)

urlpatterns = [
    # Hospitals
    path('hospitals/',                      HospitalListView.as_view(),           name='hospital-list'),
    path('hospitals/add/',                  HospitalCreateView.as_view(),         name='hospital-add'),
    path('hospitals/<uuid:pk>/',            HospitalDetailView.as_view(),         name='hospital-detail'),
    path('hospitals/nearest/<str:district>/', NearestHospitalView.as_view(),     name='nearest-hospital'),

    # Emergency requests
    path('request/',                        EmergencyRequestCreateView.as_view(), name='emergency-request'),
    path('requests/',                       EmergencyRequestListView.as_view(),   name='emergency-list'),
    path('requests/active/',               ActiveEmergenciesView.as_view(),       name='emergency-active'),
    path('requests/<uuid:pk>/status/',     EmergencyStatusUpdateView.as_view(),   name='emergency-status'),
]