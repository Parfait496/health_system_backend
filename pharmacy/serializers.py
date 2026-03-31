from rest_framework import serializers
from .models import Medication, Dispensing


class MedicationSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = Medication
        fields = [
            'id', 'name', 'generic_name', 'category',
            'description', 'unit', 'stock_quantity',
            'reorder_level', 'unit_price',
            'requires_prescription', 'is_available',
            'is_low_stock', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_low_stock']


class DispensingSerializer(serializers.ModelSerializer):
    medication_name = serializers.SerializerMethodField()
    patient_health_id = serializers.SerializerMethodField()
    dispensed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Dispensing
        fields = [
            'id', 'prescription', 'patient', 'patient_health_id',
            'medication', 'medication_name', 'quantity_dispensed',
            'status', 'notes', 'dispensed_by_name', 'dispensed_at'
        ]
        read_only_fields = ['id', 'dispensed_at']

    def get_medication_name(self, obj):
        return obj.medication.name if obj.medication else None

    def get_patient_health_id(self, obj):
        return obj.patient.health_id

    def get_dispensed_by_name(self, obj):
        if obj.dispensed_by:
            return obj.dispensed_by.get_full_name()
        return None


class DispensingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispensing
        fields = [
            'prescription', 'patient', 'medication',
            'quantity_dispensed', 'status', 'notes'
        ]

    def validate(self, attrs):
        medication = attrs.get('medication')
        quantity = attrs.get('quantity_dispensed')

        if medication and quantity:
            if medication.stock_quantity < quantity:
                raise serializers.ValidationError({
                    'quantity_dispensed': (
                        f'Insufficient stock. '
                        f'Available: {medication.stock_quantity} '
                        f'{medication.unit}.'
                    )
                })
        return attrs

    def create(self, validated_data):
        return Dispensing.objects.create(
            dispensed_by=self.context['request'].user,
            **validated_data
        )