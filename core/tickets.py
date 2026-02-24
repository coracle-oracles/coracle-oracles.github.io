import json
from pathlib import Path

_json_path = Path(__file__).parent.parent / 'tickets.json'
with open(_json_path) as f:
    ticket_types = json.load(f)
