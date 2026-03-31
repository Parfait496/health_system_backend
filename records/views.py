from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import ClinicalNote, Diagnosis, Prescription
from .serializers import (
    ClinicalNoteSerializer,
    ClinicalNoteCreateSerializer,
    DiagnosisSerializer,
    PrescriptionSerializer,
)
from Users.permissions import IsAdminOrDoctor, IsDoctor


class ClinicalNoteCreateView(generics.CreateAPIView):
    """Doctor creates a clinical note — optionally with diagnoses and prescriptions."""
    serializer_class = ClinicalNoteCreateSerializer
    permission_classes = [IsAuthenticated, IsDoctor]


class ClinicalNoteListView(generics.ListAPIView):
    """
    List clinical notes.
    - Doctor sees notes they wrote
    - Patient sees their own notes
    - Admin sees all
    Heavily optimized — prefetch diagnoses and prescriptions
    to avoid N+1 queries.
    """
    serializer_class = ClinicalNoteSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_finalized', 'patient']
    ordering_fields = ['created_at']

    def get_queryset(self):
        user = self.request.user
        qs = ClinicalNote.objects.select_related(
            'patient__user', 'doctor', 'appointment'
        ).prefetch_related(
            'diagnoses', 'prescriptions'
        )
        if user.is_admin:
            return qs.all()
        if user.is_doctor:
            return qs.filter(doctor=user)
        if user.is_patient:
            return qs.filter(patient__user=user)
        return ClinicalNote.objects.none()


class ClinicalNoteDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a clinical note.
    Cannot update if is_finalized=True.
    """
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ClinicalNoteCreateSerializer
        return ClinicalNoteSerializer

    def get_object(self):
        return get_object_or_404(
            ClinicalNote.objects.select_related(
                'patient__user', 'doctor'
            ).prefetch_related(
                'diagnoses', 'prescriptions'
            ),
            id=self.kwargs['pk']
        )


class PatientClinicalNotesView(generics.ListAPIView):
    """All clinical notes for a specific patient."""
    serializer_class = ClinicalNoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from patients.models import PatientProfile
        patient = get_object_or_404(
            PatientProfile,
            id=self.kwargs['patient_id']
        )
        user = self.request.user

        # Patients can only see their own notes
        if user.is_patient and patient.user != user:
            return ClinicalNote.objects.none()

        return ClinicalNote.objects.filter(
            patient=patient
        ).select_related(
            'doctor', 'appointment'
        ).prefetch_related(
            'diagnoses', 'prescriptions'
        )


class PatientPrescriptionsView(generics.ListAPIView):
    """
    All active prescriptions for a patient.
    Used by pharmacy to check what's been prescribed.
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']

    def get_queryset(self):
        from patients.models import PatientProfile
        patient = get_object_or_404(
            PatientProfile,
            id=self.kwargs['patient_id']
        )
        user = self.request.user

        if user.is_patient and patient.user != user:
            return Prescription.objects.none()

        return Prescription.objects.filter(
            patient=patient
        ).select_related(
            'prescribed_by', 'clinical_note'
        ).order_by('-created_at')


class PatientDiagnosesView(generics.ListAPIView):
    """All diagnoses for a patient — full medical history view."""
    serializer_class = DiagnosisSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_resolved', 'severity', 'diagnosis_type']

    def get_queryset(self):
        from patients.models import PatientProfile
        patient = get_object_or_404(
            PatientProfile,
            id=self.kwargs['patient_id']
        )
        user = self.request.user

        if user.is_patient and patient.user != user:
            return Diagnosis.objects.none()

        return Diagnosis.objects.filter(
            patient=patient
        ).select_related('diagnosed_by').order_by('-diagnosed_date')