from django.contrib import admin
from .models import PatientProfile, MedicalHistory


class MedicalHistoryInline(admin.TabularInline):
    model = MedicalHistory
    extra = 0
    readonly_fields = ['created_at']


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ['health_id', 'get_full_name', 'gender',
                    'blood_type', 'insurance_type', 'district', 'created_at']
    list_filter = ['gender', 'blood_type', 'insurance_type', 'district']
    search_fields = ['health_id', 'user__first_name',
                     'user__last_name', 'user__email']
    readonly_fields = ['health_id', 'created_at', 'updated_at']
    inlines = [MedicalHistoryInline]

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full name'


@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'event_type', 'title', 'event_date', 'recorded_by']
    list_filter = ['event_type']
    search_fields = ['patient__health_id', 'title']