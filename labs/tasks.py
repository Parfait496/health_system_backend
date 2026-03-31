from celery import shared_task


@shared_task(bind=True, max_retries=3)
def notify_lab_result_ready(self, result_id):
    """
    Triggered when a lab technician uploads a result.
    Notifies both the patient and the requesting doctor.
    """
    try:
        from .models import LabResult
        from common.email import (
            lab_result_patient_email,
            lab_result_doctor_email
        )

        result = LabResult.objects.select_related(
            'lab_test__patient__user',
            'lab_test__requested_by'
        ).get(id=result_id)

        # Notify patient
        lab_result_patient_email(result)
        result.patient_notified = True

        # Notify doctor
        if result.lab_test.requested_by:
            lab_result_doctor_email(result)
            result.doctor_notified = True

        result.save()
        return f"Notifications sent for result {result_id}"

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def flag_critical_lab_result(self, result_id):
    """
    If a result comes back as CRITICAL,
    immediately alert the requesting doctor by email.
    Critical results cannot wait for the daily digest.
    """
    try:
        from .models import LabResult
        from common.email import send_email

        result = LabResult.objects.select_related(
            'lab_test__patient__user',
            'lab_test__requested_by'
        ).get(id=result_id)

        if result.result_status != 'critical':
            return "Not critical — no alert needed"

        doctor = result.lab_test.requested_by
        if not doctor:
            return "No requesting doctor found"

        send_email(
            subject=f"CRITICAL LAB RESULT — {result.lab_test.test_name}",
            message=f"""
URGENT: Critical Lab Result

Dr. {doctor.get_full_name()},

A CRITICAL result has been returned for your patient.

Patient:       {result.lab_test.patient.health_id}
Test:          {result.lab_test.test_name}
Result:        {result.result_value} {result.unit}
Reference:     {result.reference_range}
Interpretation: {result.interpretation}

Immediate clinical review is required.

Rwanda Health System
""",
            recipient_list=[doctor.email]
        )

        return f"Critical alert sent for result {result_id}"

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)