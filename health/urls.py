from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('api/auth/', include('Users.urls')),

    # Apps (we'll fill these in per step)
    path('api/patients/', include('patients.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/records/', include('records.urls')),
    path('api/pharmacy/', include('pharmacy.urls')),
    path('api/labs/', include('labs.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/emergency/', include('emergency.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)