from rest_framework import serializers
from .models import Hospital, EmergencyRequest


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = [
            'id', 'name', 'facility_type', 'district', 'sector',
            'address', 'latitude', 'longitude', 'phone_number',
            'emergency_phone', 'has_emergency_unit', 'has_ambulance',
            'is_active', 'bed_capacity'
        ]
        read_only_fields = ['id']


class EmergencyRequestSerializer(serializers.ModelSerializer):
    assigned_hospital_name = serializers.SerializerMethodField()
    emergency_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = EmergencyRequest
        fields = [
            'id', 'patient', 'emergency_type', 'emergency_type_display',
            'status', 'status_display', 'description',
            'latitude', 'longitude', 'location_description', 'district',
            'assigned_hospital', 'assigned_hospital_name',
            'responder_notes', 'created_at', 'dispatched_at', 'resolved_at'
        ]
        read_only_fields = [
            'id', 'assigned_hospital', 'created_at',
            'dispatched_at', 'resolved_at'
        ]

    def get_assigned_hospital_name(self, obj):
        if obj.assigned_hospital:
            return obj.assigned_hospital.name
        return None

    def get_emergency_type_display(self, obj):
        return obj.get_emergency_type_display()

    def get_status_display(self, obj):
        return obj.get_status_display()

    def create(self, validated_data):
        request = self.context['request']
        user = request.user if request.user.is_authenticated else None

        emergency = EmergencyRequest.objects.create(
            requested_by=user,
            **validated_data
        )

        # Auto-assign nearest hospital with ambulance
        district = validated_data.get('district', '')
        if district:
            nearest = Hospital.objects.filter(
                district__iexact=district,
                has_ambulance=True,
                is_active=True
            ).first()
            if nearest:
                emergency.assigned_hospital = nearest
                emergency.save()

        return emergency