-- Insert Coracle 2026 event
INSERT INTO core_event (name, start_date, end_date, is_active, created_at, updated_at)
VALUES ('Coracle 2026', '2026-11-12', '2026-11-15', 1, datetime('now'), datetime('now'));

-- Insert ticket types tied to the event
INSERT INTO core_tickettype (event_id, name, label, description, price, stripe_price_id, max_per_user, created_at, updated_at)
VALUES
    ((SELECT id FROM core_event WHERE name = 'Coracle 2026'), 'adult_ticket', 'Adult Ticket', 'General admission for adults', 100, 'price_1T4U2SK9GOXEfTNqNLuPn0Av', 4, datetime('now'), datetime('now')),
    ((SELECT id FROM core_event WHERE name = 'Coracle 2026'), 'child_ticket', 'Child Ticket', 'General admission for children (12 and under)', 100, 'price_1T4U2AK9GOXEfTNqqYrHAhff', 4, datetime('now'), datetime('now')),
    ((SELECT id FROM core_event WHERE name = 'Coracle 2026'), 'vehicle_pass', 'Vehicle Pass', 'Parking pass for one vehicle', 100, 'price_1T4U2SK9GOXEfTNqNLuPn0Av', 2, datetime('now'), datetime('now'));
