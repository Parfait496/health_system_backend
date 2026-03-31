from django.urls import path
from .views import (
    ClinicalNoteCreateView,
    ClinicalNoteListView,
    ClinicalNoteDetailView,
    PatientClinicalNotesView,
    PatientPrescriptionsView,
    PatientDiagnosesView,
)

urlpatterns = [
    # Clinical notes
    path('notes/',                              ClinicalNoteCreateView.as_view(),   name='note-create'),
    path('notes/all/',                          ClinicalNoteListView.as_view(),     name='note-list'),
    path('notes/<uuid:pk>/',                    ClinicalNoteDetailView.as_view(),   name='note-detail'),

    # Per-patient views
    path('patient/<uuid:patient_id>/notes/',         PatientClinicalNotesView.as_view(),  name='patient-notes'),
    path('patient/<uuid:patient_id>/prescriptions/', PatientPrescriptionsView.as_view(),  name='patient-prescriptions'),
    path('patient/<uuid:patient_id>/diagnoses/',     PatientDiagnosesView.as_view(),      name='patient-diagnoses'),
]