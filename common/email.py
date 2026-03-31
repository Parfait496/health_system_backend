from django.core.mail import send_mail
from django.conf import settings


def send_email(subject, message, recipient_list, html_message=None):
    """
    Central email sender.
    All system emails go through here so we can
    switch providers (SendGrid, AWS SES) in one place.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def appointment_confirmation_email(appointment):
    subject = "Appointment Confirmed — Rwanda Health System"
    message = f"""
Dear {appointment.patient.user.get_full_name()},

Your appointment has been confirmed.

Details:
  Doctor:   Dr. {appointment.doctor.get_full_name()}
  Date:     {appointment.scheduled_date.strftime('%A, %d %B %Y')}
  Time:     {appointment.scheduled_time.strftime('%I:%M %p')}
  Type:     {appointment.get_appointment_type_display()}
  Queue No: {appointment.queue_number}

Please arrive 15 minutes early.

Rwanda Health System
"""
    return send_email(
        subject,
        message,
        [appointment.patient.user.email]
    )


def appointment_reminder_email(appointment):
    subject = "Reminder: Appointment Tomorrow — Rwanda Health System"
    message = f"""
Dear {appointment.patient.user.get_full_name()},

This is a reminder that you have an appointment tomorrow.

Details:
  Doctor:   Dr. {appointment.doctor.get_full_name()}
  Date:     {appointment.scheduled_date.strftime('%A, %d %B %Y')}
  Time:     {appointment.scheduled_time.strftime('%I:%M %p')}
  Queue No: {appointment.queue_number}

Rwanda Health System
"""
    return send_email(
        subject,
        message,
        [appointment.patient.user.email]
    )


def lab_result_patient_email(lab_result):
    subject = "Your Lab Result is Ready — Rwanda Health System"
    message = f"""
Dear {lab_result.lab_test.patient.user.get_full_name()},

Your lab result for {lab_result.lab_test.test_name} is now available.

Result Status: {lab_result.get_result_status_display()}

Please log in to the health portal to view your full result,
or visit your doctor for interpretation.

Rwanda Health System
"""
    return send_email(
        subject,
        message,
        [lab_result.lab_test.patient.user.email]
    )


def lab_result_doctor_email(lab_result):
    subject = f"Lab Result Ready: {lab_result.lab_test.test_name}"
    message = f"""
Dr. {lab_result.lab_test.requested_by.get_full_name()},

A lab result is ready for your patient.

Patient:       {lab_result.lab_test.patient.health_id}
Test:          {lab_result.lab_test.test_name}
Result Status: {lab_result.get_result_status_display()}
Value:         {lab_result.result_value} {lab_result.unit}
Reference:     {lab_result.reference_range}

Rwanda Health System
"""
    return send_email(
        subject,
        message,
        [lab_result.lab_test.requested_by.email]
    )


def low_stock_alert_email(medications, pharmacist_emails):
    subject = "Low Stock Alert — Rwanda Health System"
    med_list = "\n".join([
        f"  - {m.name}: {m.stock_quantity} {m.unit} remaining"
        for m in medications
    ])
    message = f"""
Pharmacy Stock Alert,

The following medications are below reorder level:

{med_list}

Please reorder as soon as possible.

Rwanda Health System
"""
    return send_email(subject, message, pharmacist_emails)