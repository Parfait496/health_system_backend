from django.contrib import admin
from .models import Hospital, EmergencyRequest


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'facility_type', 'district',
        'has_emergency_unit', 'has_ambulance', 'is_active'
    ]
    list_filter = [
        'facility_type', 'has_emergency_unit',
        'has_ambulance', 'is_active', 'district'
    ]
    search_fields = ['name', 'district', 'sector']


@admin.register(EmergencyRequest)
class EmergencyRequestAdmin(admin.ModelAdmin):
    list_display = [
        'emergency_type', 'district', 'status',
        'assigned_hospital', 'created_at'
    ]
    list_filter = ['status', 'emergency_type', 'district']
    search_fields = ['district', 'location_description']
    readonly_fields = ['created_at', 'dispatched_at', 'resolved_at']