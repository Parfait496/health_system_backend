from django.urls import path
from .views import (
    PatientProfileCreateView,
    PatientProfileMeView,
    PatientListView,
    PatientDetailView,
    MedicalHistoryCreateView,
    MedicalHistoryListView,
)

urlpatterns = [
    # Patient manages own profile
    path('profile/',              PatientProfileCreateView.as_view(), name='patient-create'),
    path('profile/me/',           PatientProfileMeView.as_view(),     name='patient-me'),

    # Doctor/admin views
    path('',                      PatientListView.as_view(),          name='patient-list'),
    path('<uuid:pk>/',            PatientDetailView.as_view(),        name='patient-detail'),

    # Medical history
    path('<uuid:patient_id>/history/',       MedicalHistoryListView.as_view(),   name='history-list'),
    path('<uuid:patient_id>/history/add/',   MedicalHistoryCreateView.as_view(), name='history-add'),
]