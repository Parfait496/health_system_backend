from rest_framework import serializers
from .models import DiseaseReport, HealthMetric


class DiseaseReportSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.SerializerMethodField()
    fatality_rate = serializers.SerializerMethodField()

    class Meta:
        model = DiseaseReport
        fields = [
            'id', 'condition_name', 'icd_code', 'district',
            'period', 'period_start', 'period_end',
            'case_count', 'death_count', 'recovered_count',
            'fatality_rate', 'is_outbreak', 'outbreak_threshold',
            'reported_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'is_outbreak', 'created_at']

    def get_reported_by_name(self, obj):
        if obj.reported_by:
            return obj.reported_by.get_full_name()
        return None

    def get_fatality_rate(self, obj):
        if obj.case_count > 0:
            return round((obj.death_count / obj.case_count) * 100, 2)
        return 0.0


class HealthMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthMetric
        fields = [
            'id', 'metric_type', 'district',
            'value', 'date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']