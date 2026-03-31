from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import PatientProfile, MedicalHistory
from .serializers import (
    PatientProfileSerializer,
    PatientProfileCreateSerializer,
    MedicalHistorySerializer
)
from .permissions import CanViewPatient
from Users.permissions import IsAdminOrDoctor, IsPatient


class PatientProfileCreateView(generics.CreateAPIView):
    """
    Patient creates their own profile after registration.
    One user can only have one profile.
    """
    serializer_class = PatientProfileCreateSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def create(self, request, *args, **kwargs):
        if PatientProfile.objects.filter(user=request.user).exists():
            return Response(
                {'error': 'Profile already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)


class PatientProfileMeView(generics.RetrieveUpdateAPIView):
    """
    Patient views and updates their own profile.
    Uses select_related to fetch user data in one DB query.
    """
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_object(self):
        return get_object_or_404(
            PatientProfile.objects.select_related('user')
                                  .prefetch_related('medical_history'),
            user=self.request.user
        )


class PatientListView(generics.ListAPIView):
    """
    Doctors and admins only — list all patients.
    Optimized with select_related to avoid N+1 queries.
    """
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]
    filterset_fields = ['gender', 'blood_type', 'insurance_type', 'district']
    search_fields = [
        'health_id', 'user__first_name',
        'user__last_name', 'user__email'
    ]
    ordering_fields = ['created_at', 'user__last_name']

    def get_queryset(self):
        return PatientProfile.objects.select_related('user') \
                                     .prefetch_related('medical_history') \
                                     .order_by('-created_at')


class PatientDetailView(generics.RetrieveAPIView):
    """
    Doctor or admin retrieves a specific patient by ID.
    """
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated, CanViewPatient]

    def get_object(self):
        profile = get_object_or_404(
            PatientProfile.objects.select_related('user')
                                  .prefetch_related('medical_history'),
            id=self.kwargs['pk']
        )
        self.check_object_permissions(self.request, profile)
        return profile


class MedicalHistoryCreateView(generics.CreateAPIView):
    """
    Doctor adds a medical history entry for a patient.
    """
    serializer_class = MedicalHistorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]

    def perform_create(self, serializer):
        patient = get_object_or_404(
            PatientProfile,
            id=self.kwargs['patient_id']
        )
        serializer.save(
            patient=patient,
            recorded_by=self.request.user
        )


class MedicalHistoryListView(generics.ListAPIView):
    """
    List all medical history entries for a patient.
    """
    serializer_class = MedicalHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = get_object_or_404(
            PatientProfile,
            id=self.kwargs['patient_id']
        )
        # Patients can only see their own history
        if self.request.user.is_patient:
            if patient.user != self.request.user:
                return MedicalHistory.objects.none()
        return MedicalHistory.objects.filter(patient=patient) \
                                     .select_related('recorded_by')