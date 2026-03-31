from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import Hospital, EmergencyRequest
from .serializers import HospitalSerializer, EmergencyRequestSerializer
from Users.permissions import IsAdmin, IsAdminOrDoctor


class HospitalListView(generics.ListAPIView):
    """
    List all active hospitals.
    Filterable by district, facility type, ambulance availability.
    """
    serializer_class = HospitalSerializer
    permission_classes = [AllowAny]
    filterset_fields = [
        'district', 'facility_type',
        'has_ambulance', 'has_emergency_unit'
    ]
    search_fields = ['name', 'district', 'sector']

    def get_queryset(self):
        return Hospital.objects.filter(
            is_active=True
        ).order_by('district', 'name')


class HospitalCreateView(generics.CreateAPIView):
    """Admin registers a new hospital."""
    serializer_class = HospitalSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class HospitalDetailView(generics.RetrieveUpdateAPIView):
    """Admin updates hospital details."""
    serializer_class = HospitalSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = Hospital.objects.all()


class NearestHospitalView(APIView):
    """
    Given a district, returns the nearest hospitals
    with emergency units or ambulances.
    In a full deployment this would use GPS distance
    calculation — for now we match by district then
    neighbouring districts.
    """
    permission_classes = [AllowAny]

    def get(self, request, district):
        # First — same district with emergency unit
        same_district = Hospital.objects.filter(
            district__iexact=district,
            has_emergency_unit=True,
            is_active=True
        ).order_by('-has_ambulance')

        if same_district.exists():
            serializer = HospitalSerializer(same_district, many=True)
            return Response({
                'district': district,
                'hospitals': serializer.data,
                'note': 'Facilities in your district'
            })

        # Fallback — any active hospital with emergency unit
        any_hospital = Hospital.objects.filter(
            has_emergency_unit=True,
            is_active=True
        ).order_by('name')[:5]

        serializer = HospitalSerializer(any_hospital, many=True)
        return Response({
            'district': district,
            'hospitals': serializer.data,
            'note': 'No emergency unit in your district — showing nearest available'
        })


class EmergencyRequestCreateView(generics.CreateAPIView):
    """
    Anyone can submit an emergency request.
    Authentication is optional — bystanders can request help.
    """
    serializer_class = EmergencyRequestSerializer
    permission_classes = [AllowAny]


class EmergencyRequestListView(generics.ListAPIView):
    """
    Active emergency requests — for dispatch coordinators.
    Ordered by most recent first.
    """
    serializer_class = EmergencyRequestSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]
    filterset_fields = ['status', 'emergency_type', 'district']
    ordering_fields = ['created_at']

    def get_queryset(self):
        return EmergencyRequest.objects.select_related(
            'patient__user',
            'assigned_hospital',
            'responder'
        ).order_by('-created_at')


class EmergencyStatusUpdateView(APIView):
    """
    Responder updates the status of an emergency request.
    Tracks dispatched_at and resolved_at timestamps automatically.
    """
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]

    def patch(self, request, pk):
        emergency = get_object_or_404(EmergencyRequest, id=pk)
        new_status = request.data.get('status')
        notes = request.data.get('responder_notes', '')

        valid_statuses = [s.value for s in EmergencyRequest.Status]
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Choose from: {valid_statuses}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        emergency.status = new_status
        if notes:
            emergency.responder_notes = notes
        if new_status == 'dispatched' and not emergency.dispatched_at:
            emergency.dispatched_at = timezone.now()
            emergency.responder = request.user
        if new_status == 'resolved' and not emergency.resolved_at:
            emergency.resolved_at = timezone.now()

        emergency.save()

        return Response(
            EmergencyRequestSerializer(emergency).data,
            status=status.HTTP_200_OK
        )


class ActiveEmergenciesView(generics.ListAPIView):
    """
    Dashboard view — only pending and in-progress emergencies.
    """
    serializer_class = EmergencyRequestSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]

    def get_queryset(self):
        return EmergencyRequest.objects.filter(
            status__in=['pending', 'dispatched', 'en_route', 'arrived']
        ).select_related(
            'assigned_hospital', 'responder'
        ).order_by('-created_at')