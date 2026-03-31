from django.contrib import admin
from .models import Medication, Dispensing


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'generic_name', 'stock_quantity',
        'reorder_level', 'unit_price', 'is_available'
    ]
    list_filter = ['is_available', 'requires_prescription', 'category']
    search_fields = ['name', 'generic_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Dispensing)
class DispensingAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'medication', 'quantity_dispensed',
        'status', 'dispensed_by', 'dispensed_at'
    ]
    list_filter = ['status']
    search_fields = ['patient__health_id', 'medication__name']
    readonly_fields = ['dispensed_at']