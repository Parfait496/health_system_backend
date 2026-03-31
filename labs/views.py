from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import LabTest, LabResult
from .serializers import (
    LabTestSerializer,
    LabTestCreateSerializer,
    LabResultCreateSerializer,
)
from Users.permissions import IsAdminOrDoctor, IsLabTech


class LabTestCreateView(generics.CreateAPIView):
    """Doctor requests a lab test for a patient."""
    serializer_class = LabTestCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]


class LabTestListView(generics.ListAPIView):
    """
    List lab tests.
    - Doctor sees tests they requested
    - Lab tech sees all pending/processing tests
    - Patient sees their own tests
    - Admin sees all
    """
    serializer_class = LabTestSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'priority']
    search_fields = ['test_name', 'patient__health_id']
    ordering_fields = ['requested_at', 'priority']

    def get_queryset(self):
        user = self.request.user
        qs = LabTest.objects.select_related(
            'patient__user', 'requested_by',
            'assigned_to'
        ).prefetch_related('result')

        if user.is_admin:
            return qs.all()
        if user.is_doctor:
            return qs.filter(requested_by=user)
        if user.is_lab_tech:
            return qs.filter(
                status__in=['requested', 'collected', 'processing']
            )
        if user.is_patient:
            return qs.filter(patient__user=user)
        return LabTest.objects.none()


class LabTestDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a lab test status."""
    serializer_class = LabTestSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(
            LabTest.objects.select_related(
                'patient__user', 'requested_by'
            ).prefetch_related('result'),
            id=self.kwargs['pk']
        )


class LabResultUploadView(generics.CreateAPIView):
    """
    Lab technician uploads a result for a test.
    Automatically marks test as completed.
    """
    serializer_class = LabResultCreateSerializer
    permission_classes = [IsAuthenticated, IsLabTech]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['lab_test'] = get_object_or_404(
            LabTest,
            id=self.kwargs['test_id']
        )
        return context
    
    def perform_create(self, serializer):
        result = serializer.save()
        # Notify patient and doctor
        from .tasks import notify_lab_result_ready, flag_critical_lab_result
        notify_lab_result_ready.delay(str(result.id))
        # Extra urgent alert for critical results
        if result.result_status == 'critical':
            flag_critical_lab_result.delay(str(result.id))


class PatientLabTestsView(generics.ListAPIView):
    """All lab tests for a specific patient."""
    serializer_class = LabTestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from patients.models import PatientProfile
        patient = get_object_or_404(
            PatientProfile,
            id=self.kwargs['patient_id']
        )
        user = self.request.user
        if user.is_patient and patient.user != user:
            return LabTest.objects.none()

        return LabTest.objects.filter(
            patient=patient
        ).select_related(
            'requested_by', 'assigned_to'
        ).prefetch_related('result')