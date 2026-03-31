from rest_framework import serializers
from django.utils import timezone
from .models import Appointment
from Users.serializers import UserSerializer
from patients.serializers import PatientProfileSerializer


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Used by patient to book an appointment."""

    class Meta:
        model = Appointment
        fields = [
            'doctor', 'appointment_type', 'scheduled_date',
            'scheduled_time', 'duration_minutes', 'reason'
        ]

    def validate(self, attrs):
        # Cannot book in the past
        scheduled_date = attrs.get('scheduled_date')
        if scheduled_date < timezone.now().date():
            raise serializers.ValidationError(
                {'scheduled_date': 'Cannot book an appointment in the past.'}
            )

        # Check doctor is not already booked at that time
        doctor = attrs.get('doctor')
        scheduled_time = attrs.get('scheduled_time')
        duration = attrs.get('duration_minutes', 30)

        conflict = Appointment.objects.filter(
            doctor=doctor,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            status__in=['pending', 'confirmed', 'in_progress']
        ).exists()

        if conflict:
            raise serializers.ValidationError(
                {'scheduled_time': 'This doctor already has an appointment at this time.'}
            )

        return attrs

    def create(self, validated_data):
        patient = self.context['request'].user.patient_profile
        return Appointment.objects.create(patient=patient, **validated_data)


class AppointmentSerializer(serializers.ModelSerializer):
    """Full appointment details — used for reading."""
    doctor_name = serializers.SerializerMethodField()
    patient_health_id = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient_health_id', 'patient_name',
            'doctor_name', 'appointment_type', 'status',
            'scheduled_date', 'scheduled_time', 'duration_minutes',
            'queue_number', 'reason', 'notes', 'doctor_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'queue_number', 'created_at', 'updated_at'
        ]

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    def get_patient_health_id(self, obj):
        return obj.patient.health_id

    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name()


class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):
    """Doctor uses this to update status and add notes."""

    class Meta:
        model = Appointment
        fields = ['status', 'doctor_notes']

    def validate_status(self, value):
        allowed = [
            Appointment.Status.CONFIRMED,
            Appointment.Status.IN_PROGRESS,
            Appointment.Status.COMPLETED,
            Appointment.Status.NO_SHOW,
            Appointment.Status.CANCELLED,
        ]
        if value not in allowed:
            raise serializers.ValidationError(
                f'Invalid status. Choose from: {[s.value for s in allowed]}'
            )
        return value