from rest_framework.permissions import BasePermission
from Users.models import User


class IsAppointmentOwner(BasePermission):
    """Patient can only access their own appointments."""
    def has_object_permission(self, request, view, obj):
        return obj.patient.user == request.user


class IsAppointmentDoctor(BasePermission):
    """Doctor can only access appointments assigned to them."""
    def has_object_permission(self, request, view, obj):
        return obj.doctor == request.user


class CanAccessAppointment(BasePermission):
    """Admin, the assigned doctor, or the patient can access."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == User.Role.ADMIN:
            return True
        if user.role == User.Role.DOCTOR:
            return obj.doctor == user
        if user.role == User.Role.PATIENT:
            return obj.patient.user == user
        return False