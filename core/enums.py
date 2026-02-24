from enum import Enum


class TicketType(str, Enum):
    ADULT = 'adult_ticket'
    CHILD = 'child_ticket'
    VEHICLE = 'vehicle_pass'

    @property
    def label(self):
        return {
            TicketType.ADULT: 'Adult Ticket',
            TicketType.CHILD: 'Child Ticket',
            TicketType.VEHICLE: 'Vehicle Pass',
        }[self]

    @property
    def description(self):
        return {
            TicketType.ADULT: 'General admission for adults',
            TicketType.CHILD: 'General admission for children (12 and under)',
            TicketType.VEHICLE: 'Parking pass for one vehicle',
        }[self]

    @property
    def price(self):
        """Price in cents."""
        return {
            TicketType.ADULT: 100,
            TicketType.CHILD: 100,
            TicketType.VEHICLE: 100,
        }[self]

    @property
    def price_id(self):
        """Stripe Price ID from settings."""
        from django.conf import settings
        return {
            TicketType.ADULT: settings.TICKET_PRICE_ADULT,
            TicketType.CHILD: settings.TICKET_PRICE_TEENAGER,
            TicketType.VEHICLE: settings.TICKET_PRICE_VEHICLE_PASS,
        }[self]
