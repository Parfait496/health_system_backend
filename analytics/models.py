import uuid
from django.db import models
from Users.models import User


class DiseaseReport(models.Model):
    """
    Aggregated disease reporting per district per period.
    Built from diagnosis data — used for outbreak detection.
    """
    class Period(models.TextChoices):
        DAILY   = 'daily',   'Daily'
        WEEKLY  = 'weekly',  'Weekly'
        MONTHLY = 'monthly', 'Monthly'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    condition_name = models.CharField(max_length=200)
    icd_code = models.CharField(max_length=20, blank=True)
    district = models.CharField(max_length=100)
    period = models.CharField(
        max_length=20,
        choices=Period.choices,
        default=Period.WEEKLY
    )
    period_start = models.DateField()
    period_end = models.DateField()
    case_count = models.PositiveIntegerField(default=0)
    death_count = models.PositiveIntegerField(default=0)
    recovered_count = models.PositiveIntegerField(default=0)

    # Outbreak flag — set automatically by analytics task
    is_outbreak = models.BooleanField(default=False)
    outbreak_threshold = models.PositiveIntegerField(
        default=10,
        help_text="Case count that triggers outbreak flag"
    )

    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='disease_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'disease_reports'
        ordering = ['-period_start']
        unique_together = ['condition_name', 'district', 'period_start', 'period']

    def __str__(self):
        return (
            f"{self.condition_name} in {self.district} "
            f"({self.period_start} — {self.period_end}): "
            f"{self.case_count} cases"
        )

    def save(self, *args, **kwargs):
        # Auto-flag outbreak
        if self.case_count >= self.outbreak_threshold:
            self.is_outbreak = True
        super().save(*args, **kwargs)


class HealthMetric(models.Model):
    """
    Tracks key health indicators per district over time.
    Used for policymaker dashboards.
    """
    class MetricType(models.TextChoices):
        APPOINTMENTS_TOTAL     = 'appointments_total',     'Total Appointments'
        APPOINTMENTS_COMPLETED = 'appointments_completed', 'Completed Appointments'
        LAB_TESTS_TOTAL        = 'lab_tests_total',        'Total Lab Tests'
        CRITICAL_RESULTS       = 'critical_results',       'Critical Lab Results'
        PRESCRIPTIONS_ISSUED   = 'prescriptions_issued',   'Prescriptions Issued'
        NEW_PATIENTS           = 'new_patients',           'New Patients Registered'
        EMERGENCY_REQUESTS     = 'emergency_requests',     'Emergency Requests'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    metric_type = models.CharField(
        max_length=50,
        choices=MetricType.choices
    )
    district = models.CharField(max_length=100, blank=True)
    value = models.PositiveIntegerField(default=0)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'health_metrics'
        ordering = ['-date']

    def __str__(self):
        return f"{self.metric_type} in {self.district} on {self.date}: {self.value}"