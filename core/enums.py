from enum import Enum


class TicketType(str, Enum):
    ADULT = 'adult_ticket'
    CHILD = 'child_ticket'
    VEHICLE = 'vehicle_pass'

    @property
    def label(self):
        labels = {
            TicketType.ADULT: 'Adult Ticket',
            TicketType.CHILD: 'Child Ticket',
            TicketType.VEHICLE: 'Vehicle Pass',
        }
        return labels[self]
