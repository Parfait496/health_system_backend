from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'queue_number', 'patient', 'doctor', 'appointment_type',
        'status', 'scheduled_date', 'scheduled_time'
    ]
    list_filter = ['status', 'appointment_type', 'scheduled_date']
    search_fields = [
        'patient__health_id',
        'patient__user__last_name',
        'doctor__last_name'
    ]
    ordering = ['scheduled_date', 'scheduled_time']
    readonly_fields = ['queue_number', 'created_at', 'updated_at']