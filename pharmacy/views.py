from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Medication, Dispensing
from .serializers import (
    MedicationSerializer,
    DispensingSerializer,
    DispensingCreateSerializer,
)
from Users.permissions import IsAdminOrDoctor, IsPharmacist


class MedicationListView(generics.ListAPIView):
    """
    Search and list available medications.
    Accessible to doctors, pharmacists, and admins.
    """
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]
    search_fields = ['name', 'generic_name', 'category']
    filterset_fields = ['is_available', 'requires_prescription']
    ordering_fields = ['name', 'stock_quantity']

    def get_queryset(self):
        return Medication.objects.filter(
            is_available=True
        ).order_by('name')


class MedicationCreateView(generics.CreateAPIView):
    """Pharmacist or admin adds a new medication to inventory."""
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated, IsPharmacist]


class MedicationDetailView(generics.RetrieveUpdateAPIView):
    """Update medication stock and details."""
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated, IsPharmacist]
    queryset = Medication.objects.all()


class LowStockView(generics.ListAPIView):
    """
    Medications below reorder level.
    Used for inventory alerts.
    """
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated, IsPharmacist]

    def get_queryset(self):
        from django.db.models import F
        return Medication.objects.filter(
            stock_quantity__lte=F('reorder_level'),
            is_available=True
        ).order_by('stock_quantity')


class DispensingCreateView(generics.CreateAPIView):
    """Pharmacist dispenses medication against a prescription."""
    serializer_class = DispensingCreateSerializer
    permission_classes = [IsAuthenticated, IsPharmacist]


class DispensingListView(generics.ListAPIView):
    """
    List all dispensing records.
    Pharmacist sees all, patient sees their own.
    """
    serializer_class = DispensingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']
    ordering_fields = ['dispensed_at']

    def get_queryset(self):
        user = self.request.user
        qs = Dispensing.objects.select_related(
            'patient__user',
            'medication',
            'dispensed_by',
            'prescription'
        )
        if user.is_admin or user.is_pharmacist:
            return qs.all()
        if user.is_patient:
            return qs.filter(patient__user=user)
        return Dispensing.objects.none()


class PatientPrescriptionQueueView(generics.ListAPIView):
    """
    Pharmacist looks up all active prescriptions
    for a patient by health ID — ready to dispense.
    """
    serializer_class = DispensingSerializer
    permission_classes = [IsAuthenticated, IsPharmacist]

    def get_queryset(self):
        from records.models import Prescription
        health_id = self.kwargs['health_id']
        return Prescription.objects.filter(
            patient__health_id=health_id,
            status='active'
        ).select_related(
            'patient__user', 'prescribed_by'
        )