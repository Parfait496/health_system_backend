from django.contrib import admin
from .models import LabTest, LabResult


class LabResultInline(admin.StackedInline):
    model = LabResult
    extra = 0
    readonly_fields = ['performed_at']


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = [
        'test_name', 'patient', 'requested_by',
        'priority', 'status', 'requested_at'
    ]
    list_filter = ['status', 'priority']
    search_fields = ['test_name', 'patient__health_id']
    readonly_fields = ['requested_at', 'collected_at', 'completed_at']
    inlines = [LabResultInline]


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = [
        'lab_test', 'result_status',
        'patient_notified', 'performed_at'
    ]
    list_filter = ['result_status', 'patient_notified']