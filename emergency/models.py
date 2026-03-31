import uuid
from django.db import models
from Users.models import User
from patients.models import PatientProfile


class Hospital(models.Model):
    """
    Registered hospitals and health centers in Rwanda.
    Used for nearest facility detection.
    """
    class FacilityType(models.TextChoices):
        REFERRAL_HOSPITAL = 'referral_hospital', 'Referral Hospital'
        DISTRICT_HOSPITAL = 'district_hospital', 'District Hospital'
        HEALTH_CENTER     = 'health_center',     'Health Center'
        CLINIC            = 'clinic',            'Clinic'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=200)
    facility_type = models.CharField(
        max_length=30,
        choices=FacilityType.choices
    )
    district = models.CharField(max_length=100)
    sector = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    # GPS coordinates
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True, blank=True
    )

    phone_number = models.CharField(max_length=20, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    has_emergency_unit = models.BooleanField(default=False)
    has_ambulance = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    bed_capacity = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hospitals'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.district})"


class EmergencyRequest(models.Model):
    """
    Patient or bystander submits an emergency request.
    Dispatched to nearest hospital with ambulance.
    """
    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending'
        DISPATCHED = 'dispatched', 'Ambulance Dispatched'
        EN_ROUTE   = 'en_route',   'En Route'
        ARRIVED    = 'arrived',    'Arrived at Scene'
        RESOLVED   = 'resolved',   'Resolved'
        CANCELLED  = 'cancelled',  'Cancelled'

    class EmergencyType(models.TextChoices):
        ACCIDENT     = 'accident',     'Road Accident'
        CARDIAC      = 'cardiac',      'Cardiac Emergency'
        STROKE       = 'stroke',       'Stroke'
        TRAUMA       = 'trauma',       'Physical Trauma'
        OBSTETRIC    = 'obstetric',    'Obstetric Emergency'
        RESPIRATORY  = 'respiratory',  'Respiratory Distress'
        OTHER        = 'other',        'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Patient (optional — bystanders can request without login)
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='emergency_requests'
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='emergency_requests_made'
    )

    emergency_type = models.CharField(
        max_length=20,
        choices=EmergencyType.choices,
        default=EmergencyType.OTHER
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    description = models.TextField()

    # Location of emergency
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True, blank=True
    )
    location_description = models.TextField(
        blank=True,
        help_text="e.g. Near Kimironko market, Gasabo district"
    )
    district = models.CharField(max_length=100, blank=True)

    # Assigned hospital
    assigned_hospital = models.ForeignKey(
        Hospital,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='emergency_requests'
    )

    # Responder
    responder = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='emergencies_handled'
    )
    responder_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'emergency_requests'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"{self.get_emergency_type_display()} — "
            f"{self.district} [{self.status}]"
        )