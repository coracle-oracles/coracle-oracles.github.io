from django.urls import path

from . import views

# Global URL patterns (not event or organizer scoped)
urlpatterns = [
    path('', views.home, name='home'),
    path('survival-guide/', views.survival_guide, name='survival_guide'),
    path('10-principles/', views.principles, name='principles'),
    path('ticket-info/', views.ticket_info, name='ticket_info'),
]
