from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import DiseaseReport, HealthMetric
from .serializers import DiseaseReportSerializer, HealthMetricSerializer
from Users.permissions import IsAdmin, IsAdminOrDoctor


class DiseaseReportCreateView(generics.CreateAPIView):
    """Admin or doctor submits a disease report."""
    serializer_class = DiseaseReportSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)


class DiseaseReportListView(generics.ListAPIView):
    """
    List all disease reports.
    Supports filtering by district, condition, outbreak status.
    """
    serializer_class = DiseaseReportSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]
    filterset_fields = ['district', 'condition_name', 'is_outbreak', 'period']
    search_fields = ['condition_name', 'icd_code', 'district']
    ordering_fields = ['case_count', 'period_start']

    def get_queryset(self):
        return DiseaseReport.objects.select_related(
            'reported_by'
        ).order_by('-period_start')


class OutbreakAlertView(generics.ListAPIView):
    """
    Active outbreaks only — for real-time alert dashboard.
    Returns all reports flagged as outbreaks in the last 30 days.
    """
    serializer_class = DiseaseReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cutoff = timezone.now().date() - timedelta(days=30)
        return DiseaseReport.objects.filter(
            is_outbreak=True,
            period_start__gte=cutoff
        ).select_related('reported_by').order_by('-case_count')


class DashboardSummaryView(APIView):
    """
    Main policymaker dashboard.
    Returns aggregated health metrics for the last 30 days.
    Uses optimized aggregation queries — no N+1 issues.
    """
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]

    def get(self, request):
        from patients.models import PatientProfile
        from appointments.models import Appointment
        from labs.models import LabTest, LabResult
        from records.models import Prescription

        today = timezone.now().date()
        last_30 = today - timedelta(days=30)
        last_7 = today - timedelta(days=7)

        # All queries use aggregation — single DB hit each
        total_patients = PatientProfile.objects.count()

        new_patients_30d = PatientProfile.objects.filter(
            created_at__date__gte=last_30
        ).count()

        appointments_30d = Appointment.objects.filter(
            scheduled_date__gte=last_30
        ).aggregate(
            total=Count('id'),
            completed=Count('id', filter=__import__(
                'django.db.models',
                fromlist=['Q']
            ).Q(status='completed')),
            cancelled=Count('id', filter=__import__(
                'django.db.models',
                fromlist=['Q']
            ).Q(status='cancelled'))
        )

        lab_stats = LabResult.objects.filter(
            performed_at__date__gte=last_30
        ).aggregate(
            total=Count('id'),
            critical=Count('id', filter=__import__(
                'django.db.models',
                fromlist=['Q']
            ).Q(result_status='critical'))
        )

        active_prescriptions = Prescription.objects.filter(
            status='active'
        ).count()

        outbreaks = DiseaseReport.objects.filter(
            is_outbreak=True,
            period_start__gte=last_30
        ).count()

        # District breakdown — which districts have most patients
        district_breakdown = PatientProfile.objects.filter(
            district__isnull=False
        ).exclude(
            district=''
        ).values('district').annotate(
            patient_count=Count('id')
        ).order_by('-patient_count')[:10]

        # Top conditions from diagnoses in last 30 days
        from records.models import Diagnosis
        top_conditions = Diagnosis.objects.filter(
            created_at__date__gte=last_30
        ).values('condition_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return Response({
            'summary': {
                'total_patients': total_patients,
                'new_patients_last_30_days': new_patients_30d,
                'active_prescriptions': active_prescriptions,
                'active_outbreaks': outbreaks,
            },
            'appointments_last_30_days': {
                'total': appointments_30d['total'],
                'completed': appointments_30d['completed'],
                'cancelled': appointments_30d['cancelled'],
            },
            'lab_results_last_30_days': {
                'total': lab_stats['total'],
                'critical': lab_stats['critical'],
            },
            'top_districts_by_patients': list(district_breakdown),
            'top_conditions_last_30_days': list(top_conditions),
            'generated_at': timezone.now(),
        })


class RegionalInsightView(APIView):
    """
    Breakdown of health metrics for a specific district.
    Used for regional health authority dashboards.
    """
    permission_classes = [IsAuthenticated, IsAdminOrDoctor]

    def get(self, request, district):
        from patients.models import PatientProfile
        from appointments.models import Appointment
        from records.models import Diagnosis
        from django.db.models import Q

        last_30 = timezone.now().date() - timedelta(days=30)

        patients = PatientProfile.objects.filter(
            district__iexact=district
        )

        patient_ids = patients.values_list('id', flat=True)

        appointments = Appointment.objects.filter(
            patient__in=patient_ids,
            scheduled_date__gte=last_30
        ).aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed'))
        )

        diagnoses = Diagnosis.objects.filter(
            patient__in=patient_ids,
            created_at__date__gte=last_30
        ).values('condition_name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        blood_types = patients.exclude(
            blood_type=''
        ).values('blood_type').annotate(
            count=Count('id')
        ).order_by('-count')

        insurance = patients.values(
            'insurance_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'district': district,
            'total_patients': patients.count(),
            'appointments_last_30_days': appointments,
            'top_diagnoses': list(diagnoses),
            'blood_type_distribution': list(blood_types),
            'insurance_distribution': list(insurance),
        })


class HealthMetricListView(generics.ListAPIView):
    serializer_class = HealthMetricSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ['metric_type', 'district', 'date']
    ordering_fields = ['date', 'value']

    def get_queryset(self):
        return HealthMetric.objects.order_by('-date')