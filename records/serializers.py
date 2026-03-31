from rest_framework import serializers
from django.utils import timezone
from .models import ClinicalNote, Diagnosis, Prescription


class DiagnosisSerializer(serializers.ModelSerializer):
    diagnosed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Diagnosis
        fields = [
            'id', 'icd_code', 'condition_name', 'diagnosis_type',
            'severity', 'notes', 'diagnosed_date', 'is_resolved',
            'resolved_date', 'diagnosed_by_name'
        ]
        read_only_fields = ['id', 'diagnosed_date']

    def get_diagnosed_by_name(self, obj):
        if obj.diagnosed_by:
            return f"Dr. {obj.diagnosed_by.get_full_name()}"
        return None


class PrescriptionSerializer(serializers.ModelSerializer):
    prescribed_by_name = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            'id', 'medication_name', 'dosage', 'frequency',
            'duration_days', 'quantity', 'instructions',
            'status', 'start_date', 'end_date',
            'prescribed_by_name', 'is_expired', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_prescribed_by_name(self, obj):
        if obj.prescribed_by:
            return f"Dr. {obj.prescribed_by.get_full_name()}"
        return None

    def get_is_expired(self, obj):
        return obj.end_date < timezone.now().date()


class ClinicalNoteSerializer(serializers.ModelSerializer):
    """Full note with nested diagnoses and prescriptions."""
    diagnoses = DiagnosisSerializer(many=True, read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)
    doctor_name = serializers.SerializerMethodField()
    patient_health_id = serializers.SerializerMethodField()
    bmi = serializers.ReadOnlyField()

    class Meta:
        model = ClinicalNote
        fields = [
            'id', 'patient_health_id', 'doctor_name', 'appointment',
            'subjective', 'objective', 'assessment', 'plan',
            'temperature', 'blood_pressure_systolic',
            'blood_pressure_diastolic', 'pulse_rate',
            'respiratory_rate', 'oxygen_saturation',
            'weight_kg', 'height_cm', 'bmi',
            'is_finalized', 'diagnoses', 'prescriptions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'bmi']

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    def get_patient_health_id(self, obj):
        return obj.patient.health_id


class ClinicalNoteCreateSerializer(serializers.ModelSerializer):
    """Used by doctor to create a note."""
    diagnoses = DiagnosisSerializer(many=True, required=False)
    prescriptions = PrescriptionSerializer(many=True, required=False)

    class Meta:
        model = ClinicalNote
        fields = [
            'patient', 'appointment',
            'subjective', 'objective', 'assessment', 'plan',
            'temperature', 'blood_pressure_systolic',
            'blood_pressure_diastolic', 'pulse_rate',
            'respiratory_rate', 'oxygen_saturation',
            'weight_kg', 'height_cm',
            'is_finalized', 'diagnoses', 'prescriptions'
        ]

    def create(self, validated_data):
        diagnoses_data = validated_data.pop('diagnoses', [])
        prescriptions_data = validated_data.pop('prescriptions', [])
        doctor = self.context['request'].user

        note = ClinicalNote.objects.create(
            doctor=doctor,
            **validated_data
        )

        # Create diagnoses
        for d in diagnoses_data:
            Diagnosis.objects.create(
                clinical_note=note,
                patient=note.patient,
                diagnosed_by=doctor,
                **d
            )

        # Create prescriptions
        for p in prescriptions_data:
            Prescription.objects.create(
                clinical_note=note,
                patient=note.patient,
                prescribed_by=doctor,
                **p
            )

        return note

    def validate(self, attrs):
        # Cannot edit a finalized note
        if self.instance and self.instance.is_finalized:
            raise serializers.ValidationError(
                'This note has been finalized and cannot be edited.'
            )
        return attrs