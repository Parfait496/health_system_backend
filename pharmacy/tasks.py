from celery import shared_task


@shared_task(bind=True, max_retries=3)
def check_low_stock_alert(self):
    """
    Runs every day at 8 AM.
    Finds medications below reorder level and
    emails all pharmacists.
    """
    try:
        from django.db.models import F
        from .models import Medication
        from Users.models import User
        from common.email import low_stock_alert_email

        low_stock = Medication.objects.filter(
            stock_quantity__lte=F('reorder_level'),
            is_available=True
        )

        if not low_stock.exists():
            return "All medications adequately stocked"

        pharmacists = User.objects.filter(
            role='pharmacist',
            is_active=True
        ).values_list('email', flat=True)

        if pharmacists:
            low_stock_alert_email(low_stock, list(pharmacists))

        return (
            f"Low stock alert sent for "
            f"{low_stock.count()} medication(s)"
        )

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task
def expire_old_prescriptions():
    """
    Runs daily.
    Marks prescriptions whose end_date has passed as expired.
    """
    from django.utils import timezone
    from records.models import Prescription

    today = timezone.now().date()
    expired = Prescription.objects.filter(
        status='active',
        end_date__lt=today
    )
    count = expired.count()
    expired.update(status='expired')
    return f"Expired {count} prescription(s)"