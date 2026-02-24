from django.db import models
from django.contrib.auth.models import User

from .enums import TicketType


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    purchasing_user = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='purchased_orders')
    owning_user = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='owned_orders')
    ticket_type = models.CharField(max_length=100, choices=[(t.value, t.label) for t in TicketType])

    stripe_checkout_session_id = models.CharField(max_length=255)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} - {self.owning_user.username} - {self.ticket_type}"
