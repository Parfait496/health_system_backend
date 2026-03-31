from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task(bind=True, max_retries=3)
def send_appointment_confirmation(self, appointment_id):
    """
    Triggered immediately when an appointment is confirmed.
    Retries up to 3 times if email fails.
    """
    try:
        from .models import Appointment
        from common.email import appointment_confirmation_email

        appointment = Appointment.objects.select_related(
            'patient__user', 'doctor'
        ).get(id=appointment_id)

        appointment_confirmation_email(appointment)

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_appointment_reminders(self):
    """
    Runs every hour.
    Finds appointments scheduled for tomorrow and
    sends reminder emails to patients who haven't
    been reminded yet.
    """
    try:
        from .models import Appointment
        from common.email import appointment_reminder_email

        tomorrow = timezone.now().date() + timedelta(days=1)

        appointments = Appointment.objects.select_related(
            'patient__user', 'doctor'
        ).filter(
            scheduled_date=tomorrow,
            status__in=['confirmed', 'pending']
        )

        sent = 0
        for appointment in appointments:
            appointment_reminder_email(appointment)
            sent += 1

        return f"Sent {sent} reminder(s) for {tomorrow}"

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_daily_digest(self):
    """
    Runs every day at 7 AM.
    Sends each doctor a summary of their appointments for today.
    """
    try:
        from .models import Appointment
        from common.email import send_email
        from users.models import User

        today = timezone.now().date()
        doctors = User.objects.filter(role='doctor', is_active=True)

        for doctor in doctors:
            appointments = Appointment.objects.select_related(
                'patient__user'
            ).filter(
                doctor=doctor,
                scheduled_date=today,
                status__in=['pending', 'confirmed']
            ).order_by('queue_number')

            if not appointments.exists():
                continue

            appt_lines = "\n".join([
                f"  [{a.queue_number}] {a.patient.user.get_full_name()} "
                f"at {a.scheduled_time.strftime('%I:%M %p')} — {a.reason[:50]}"
                for a in appointments
            ])

            message = f"""
Good morning, Dr. {doctor.get_full_name()},

You have {appointments.count()} appointment(s) today ({today.strftime('%A, %d %B %Y')}):

{appt_lines}

Rwanda Health System
"""
            send_email(
                subject=f"Your Appointments for Today — {today}",
                message=message,
                recipient_list=[doctor.email]
            )

        return f"Daily digest sent to {doctors.count()} doctor(s)"

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task
def cancel_expired_pending_appointments():
    """
    Runs daily.
    Auto-cancels appointments that stayed 'pending'
    for more than 48 hours without being confirmed.
    """
    from .models import Appointment

    cutoff = timezone.now() - timedelta(hours=48)
    expired = Appointment.objects.filter(
        status='pending',
        created_at__lt=cutoff
    )
    count = expired.count()
    expired.update(status='cancelled')
    return f"Auto-cancelled {count} expired pending appointment(s)"