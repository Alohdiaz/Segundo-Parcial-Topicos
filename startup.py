from typing import List
from models import User, Zone

demo_user = User(id=1, email="demo@iberopuebla.mx", api_key="testkey", balance=300)

zones: List[Zone] = [
    Zone(id=1, name="A", rate_per_min=1.5, max_minutes=120),
    Zone(id=2, name="B", rate_per_min=1.0, max_minutes=180),
]