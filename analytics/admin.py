from django.contrib import admin
from .models import DiseaseReport, HealthMetric


@admin.register(DiseaseReport)
class DiseaseReportAdmin(admin.ModelAdmin):
    list_display = [
        'condition_name', 'district', 'period',
        'case_count', 'death_count', 'is_outbreak', 'period_start'
    ]
    list_filter = ['is_outbreak', 'period', 'district']
    search_fields = ['condition_name', 'icd_code', 'district']
    readonly_fields = ['created_at']


@admin.register(HealthMetric)
class HealthMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'district', 'value', 'date']
    list_filter = ['metric_type', 'district']
    ordering = ['-date']