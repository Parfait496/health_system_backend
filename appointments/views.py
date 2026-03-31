from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Appointment
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentSerializer,
    AppointmentStatusUpdateSerializer,
)
from .permissions import CanAccessAppointment
from Users.permissions import IsAdminOrDoctor, IsPatient


class AppointmentCreateView(generics.CreateAPIView):
    """Patient books a new appointment."""
    serializer_class = AppointmentCreateSerializer
    permission_classes = [IsAuthenticated, IsPatient]


class AppointmentListView(generics.ListAPIView):
    """
    Returns appointments relevant to the logged-in user.
    - Patient sees their own appointments
    - Doctor sees their assigned appointments
    - Admin sees all
    Uses select_related to avoid N+1 queries.
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'appointment_type', 'scheduled_date']
    search_fields = ['patient__health_id', 'patient__user__last_name']
    ordering_fields = ['scheduled_date', 'scheduled_time', 'queue_number']

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.select_related(
            'patient__user', 'doctor'
        )
        if user.is_admin:
            return qs.all()
        if user.is_doctor:
            return qs.filter(doctor=user)
        if user.is_patient:
            return qs.filter(patient__user=user)
        return Appointment.objects.none()


class AppointmentDetailView(generics.RetrieveAPIView):
    """Retrieve a single appointment."""
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, CanAccessAppointment]

    def get_object(self):
        appointment = get_object_or_404(
            Appointment.objects.select_related('patient__user', 'doctor'),
            id=self.kwargs['pk']
        )
        self.check_object_permissions(self.request, appointment)
        return appointment


class AppointmentStatusUpdateView(generics.UpdateAPIView):
    """Doctor updates the status and adds notes."""
    serializer_class = AppointmentStatusUpdateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]
    http_method_names = ['patch']

    def get_object(self):
        appointment = get_object_or_404(
            Appointment,
            id=self.kwargs['pk']
        )
        # Doctor can only update their own appointments
        if self.request.user.is_doctor:
            if appointment.doctor != self.request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(
                    'You can only update your own appointments.'
                )
        return appointment
    def perform_update(self, serializer):
        appointment = serializer.save()
        # Fire confirmation email when doctor confirms
        if appointment.status == 'confirmed':
            from .tasks import send_appointment_confirmation
            send_appointment_confirmation.delay(str(appointment.id))


class AppointmentCancelView(APIView):
    """Patient cancels their own appointment."""
    permission_classes = [IsAuthenticated, IsPatient]

    def patch(self, request, pk):
        appointment = get_object_or_404(
            Appointment,
            id=pk,
            patient__user=request.user
        )
        if appointment.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'Cannot cancel a {appointment.status} appointment.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        return Response(
            {'message': 'Appointment cancelled successfully.'},
            status=status.HTTP_200_OK
        )


class TodayQueueView(generics.ListAPIView):
    """
    Doctor sees today's queue — ordered by queue number.
    Shows only confirmed and pending appointments for today.
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]

    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()
        qs = Appointment.objects.select_related(
            'patient__user', 'doctor'
        ).filter(
            scheduled_date=today,
            status__in=['pending', 'confirmed']
        ).order_by('queue_number')

        if user.is_doctor:
            return qs.filter(doctor=user)
        return qs