from rest_framework import serializers
from .models import LabTest, LabResult


class LabResultSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LabResult
        fields = [
            'id', 'result_value', 'unit', 'reference_range',
            'result_status', 'interpretation', 'report_file',
            'patient_notified', 'doctor_notified',
            'performed_by_name', 'performed_at'
        ]
        read_only_fields = [
            'id', 'patient_notified',
            'doctor_notified', 'performed_at'
        ]

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return obj.performed_by.get_full_name()
        return None


class LabTestSerializer(serializers.ModelSerializer):
    result = LabResultSerializer(read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    patient_health_id = serializers.SerializerMethodField()

    class Meta:
        model = LabTest
        fields = [
            'id', 'patient', 'patient_health_id', 'test_name',
            'test_code', 'description', 'priority', 'status',
            'clinical_notes', 'fasting_required',
            'requested_by_name', 'assigned_to',
            'requested_at', 'collected_at', 'completed_at',
            'result'
        ]
        read_only_fields = [
            'id', 'requested_at',
            'collected_at', 'completed_at'
        ]

    def get_requested_by_name(self, obj):
        if obj.requested_by:
            return f"Dr. {obj.requested_by.get_full_name()}"
        return None

    def get_patient_health_id(self, obj):
        return obj.patient.health_id


class LabTestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest
        fields = [
            'patient', 'test_name', 'test_code',
            'description', 'priority', 'clinical_notes',
            'fasting_required'
        ]

    def create(self, validated_data):
        return LabTest.objects.create(
            requested_by=self.context['request'].user,
            **validated_data
        )


class LabResultCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = [
            'result_value', 'unit', 'reference_range',
            'result_status', 'interpretation', 'report_file'
        ]

    def create(self, validated_data):
        from django.utils import timezone
        lab_test = self.context['lab_test']
        lab_tech = self.context['request'].user

        # Mark test as completed
        lab_test.status = LabTest.Status.COMPLETED
        lab_test.completed_at = timezone.now()
        lab_test.save()

        return LabResult.objects.create(
            lab_test=lab_test,
            performed_by=lab_tech,
            **validated_data
        )