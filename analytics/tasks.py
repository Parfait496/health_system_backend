from celery import shared_task


@shared_task
def compute_daily_health_metrics():
    """
    Runs every night at midnight.
    Computes and stores daily health metrics per district.
    Used to build trend charts over time.
    """
    from django.utils import timezone
    from django.db.models import Count
    from patients.models import PatientProfile
    from appointments.models import Appointment
    from labs.models import LabResult
    from records.models import Prescription
    from .models import HealthMetric

    today = timezone.now().date()

    # New patients registered today
    new_patients = PatientProfile.objects.filter(
        created_at__date=today
    ).values('district').annotate(count=Count('id'))

    for row in new_patients:
        HealthMetric.objects.update_or_create(
            metric_type='new_patients',
            district=row['district'] or 'Unknown',
            date=today,
            defaults={'value': row['count']}
        )

    # Appointments completed today
    completed = Appointment.objects.filter(
        scheduled_date=today,
        status='completed'
    ).count()

    HealthMetric.objects.update_or_create(
        metric_type='appointments_completed',
        district='',
        date=today,
        defaults={'value': completed}
    )

    # Critical lab results today
    critical = LabResult.objects.filter(
        performed_at__date=today,
        result_status='critical'
    ).count()

    HealthMetric.objects.update_or_create(
        metric_type='critical_results',
        district='',
        date=today,
        defaults={'value': critical}
    )

    return f"Daily metrics computed for {today}"


@shared_task
def detect_outbreaks():
    """
    Runs every 6 hours.
    Scans recent disease reports and flags any
    condition in any district where case count
    has doubled in the last 7 days.
    """
    from django.utils import timezone
    from django.db.models import Sum
    from datetime import timedelta
    from .models import DiseaseReport

    today = timezone.now().date()
    last_7 = today - timedelta(days=7)
    prev_7 = last_7 - timedelta(days=7)

    conditions = DiseaseReport.objects.values(
        'condition_name', 'district'
    ).distinct()

    flagged = 0
    for item in conditions:
        recent = DiseaseReport.objects.filter(
            condition_name=item['condition_name'],
            district=item['district'],
            period_start__gte=last_7
        ).aggregate(total=Sum('case_count'))['total'] or 0

        previous = DiseaseReport.objects.filter(
            condition_name=item['condition_name'],
            district=item['district'],
            period_start__gte=prev_7,
            period_start__lt=last_7
        ).aggregate(total=Sum('case_count'))['total'] or 0

        # Flag as outbreak if cases doubled and >= 5
        if previous > 0 and recent >= previous * 2 and recent >= 5:
            DiseaseReport.objects.filter(
                condition_name=item['condition_name'],
                district=item['district'],
                period_start__gte=last_7
            ).update(is_outbreak=True)
            flagged += 1

    return f"Outbreak detection complete. {flagged} condition(s) flagged."