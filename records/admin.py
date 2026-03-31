from django.contrib import admin
from .models import ClinicalNote, Diagnosis, Prescription


class DiagnosisInline(admin.TabularInline):
    model = Diagnosis
    extra = 0
    readonly_fields = ['diagnosed_date', 'diagnosed_by']


class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 0
    readonly_fields = ['created_at', 'prescribed_by']


@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'doctor', 'is_finalized', 'created_at'
    ]
    list_filter = ['is_finalized', 'created_at']
    search_fields = [
        'patient__health_id',
        'doctor__last_name',
    ]
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DiagnosisInline, PrescriptionInline]


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = [
        'condition_name', 'icd_code', 'patient',
        'severity', 'is_resolved', 'diagnosed_date'
    ]
    list_filter = ['severity', 'diagnosis_type', 'is_resolved']
    search_fields = ['condition_name', 'icd_code', 'patient__health_id']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = [
        'medication_name', 'dosage', 'patient',
        'status', 'start_date', 'end_date'
    ]
    list_filter = ['status', 'frequency']
    search_fields = ['medication_name', 'patient__health_id']
    readonly_fields = ['created_at']