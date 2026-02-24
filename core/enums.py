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
            TicketType.ADULT: 19000,
            TicketType.CHILD: 8500,
            TicketType.VEHICLE: 1500,
        }[self]
