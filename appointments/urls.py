from django.urls import path
from .views import (
    AppointmentCreateView,
    AppointmentListView,
    AppointmentDetailView,
    AppointmentStatusUpdateView,
    AppointmentCancelView,
    TodayQueueView,
)

urlpatterns = [
    path('',                          AppointmentListView.as_view(),        name='appointment-list'),
    path('book/',                     AppointmentCreateView.as_view(),      name='appointment-book'),
    path('<uuid:pk>/',                AppointmentDetailView.as_view(),      name='appointment-detail'),
    path('<uuid:pk>/status/',         AppointmentStatusUpdateView.as_view(), name='appointment-status'),
    path('<uuid:pk>/cancel/',         AppointmentCancelView.as_view(),      name='appointment-cancel'),
    path('queue/today/',              TodayQueueView.as_view(),             name='today-queue'),
]