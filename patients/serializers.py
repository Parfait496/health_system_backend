from rest_framework import serializers
from .models import PatientProfile, MedicalHistory
from Users.serializers import UserSerializer


class MedicalHistorySerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MedicalHistory
        fields = [
            'id', 'event_type', 'title', 'description',
            'event_date', 'recorded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return obj.recorded_by.get_full_name()
        return None


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    medical_history = MedicalHistorySerializer(many=True, read_only=True)
    age = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = [
            'id', 'health_id', 'user', 'date_of_birth', 'age',
            'gender', 'address', 'district', 'sector',
            'blood_type', 'allergies', 'chronic_conditions',
            'current_medications', 'insurance_type', 'insurance_number',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relation', 'medical_history',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'health_id', 'created_at', 'updated_at']

    def get_age(self, obj):
        if not obj.date_of_birth:
            return None
        from django.utils import timezone
        today = timezone.now().date()
        born = obj.date_of_birth
        return today.year - born.year - (
            (today.month, today.day) < (born.month, born.day)
        )


class PatientProfileCreateSerializer(serializers.ModelSerializer):
    """Used when creating a profile — excludes read-only nested fields."""
    class Meta:
        model = PatientProfile
        fields = [
            'date_of_birth', 'gender', 'address', 'district', 'sector',
            'blood_type', 'allergies', 'chronic_conditions',
            'current_medications', 'insurance_type', 'insurance_number',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relation'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        return PatientProfile.objects.create(user=user, **validated_data)