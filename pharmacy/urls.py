from django.urls import path
from .views import (
    MedicationListView,
    MedicationCreateView,
    MedicationDetailView,
    LowStockView,
    DispensingCreateView,
    DispensingListView,
    PatientPrescriptionQueueView,
)

urlpatterns = [
    path('medications/',                        MedicationListView.as_view(),           name='medication-list'),
    path('medications/add/',                    MedicationCreateView.as_view(),         name='medication-add'),
    path('medications/<uuid:pk>/',              MedicationDetailView.as_view(),         name='medication-detail'),
    path('medications/low-stock/',              LowStockView.as_view(),                 name='low-stock'),
    path('dispense/',                           DispensingCreateView.as_view(),         name='dispense'),
    path('dispensings/',                        DispensingListView.as_view(),           name='dispensing-list'),
    path('queue/<str:health_id>/',              PatientPrescriptionQueueView.as_view(), name='prescription-queue'),
]