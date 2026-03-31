import uuid
from django.db import models
from Users.models import User
from patients.models import PatientProfile


class Appointment(models.Model):

    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending'
        CONFIRMED  = 'confirmed',  'Confirmed'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED  = 'completed',  'Completed'
        CANCELLED  = 'cancelled',  'Cancelled'
        NO_SHOW    = 'no_show',    'No Show'

    class AppointmentType(models.TextChoices):
        IN_PERSON    = 'in_person',    'In Person'
        TELECONSULT  = 'teleconsult',  'Teleconsultation'
        FOLLOW_UP    = 'follow_up',    'Follow Up'
        EMERGENCY    = 'emergency',    'Emergency'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_appointments',
        limit_choices_to={'role': 'doctor'}
    )

    appointment_type = models.CharField(
        max_length=20,
        choices=AppointmentType.choices,
        default=AppointmentType.IN_PERSON
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=30)

    queue_number = models.PositiveIntegerField(null=True, blank=True)

    reason = models.TextField()
    notes = models.TextField(blank=True)
    doctor_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appointments'
        ordering = ['scheduled_date', 'scheduled_time']

    def __str__(self):
        return (
            f"{self.patient.health_id} with Dr.{self.doctor.get_full_name()} "
            f"on {self.scheduled_date} at {self.scheduled_time}"
        )

    def save(self, *args, **kwargs):
        if not self.queue_number:
            self.queue_number = self._generate_queue_number()
        super().save(*args, **kwargs)

    def _generate_queue_number(self):
        """
        Queue number resets every day per doctor.
        So doctor A can have queue 1, 2, 3 on Monday
        and restart from 1 on Tuesday.
        """
        last = Appointment.objects.filter(
            doctor=self.doctor,
            scheduled_date=self.scheduled_date
        ).order_by('queue_number').last()

        if last and last.queue_number:
            return last.queue_number + 1
        return 1