from django.urls import path
from .views import (
    LabTestCreateView,
    LabTestListView,
    LabTestDetailView,
    LabResultUploadView,
    PatientLabTestsView,
)

urlpatterns = [
    path('',                                    LabTestListView.as_view(),    name='lab-list'),
    path('request/',                            LabTestCreateView.as_view(),  name='lab-request'),
    path('<uuid:pk>/',                          LabTestDetailView.as_view(),  name='lab-detail'),
    path('<uuid:test_id>/result/',              LabResultUploadView.as_view(), name='lab-result-upload'),
    path('patient/<uuid:patient_id>/',          PatientLabTestsView.as_view(), name='patient-labs'),
]