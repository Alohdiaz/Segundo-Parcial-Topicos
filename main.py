from fastapi import FastAPI, HTTPException, Header, Depends
from models import User, Zone, Vehicle, ParkingSession, ZoneCreate, VehicleCreate
from typing import List, Optional
from math import ceil
from datetime import datetime, timezone
from database import init_db
from startup import demo_user, zones

app = FastAPI()
init_db()

vehicles: List[Vehicle] = []
sessions: List[ParkingSession] = []

next_zone_id = 3
next_vehicle_id = 1
next_session_id = 1

def get_current_user(x_api_key: str = Header(...)):
    if x_api_key != demo_user.api_key:
        raise HTTPException(status_code=401, detail="API key requerida o inválida")
    return demo_user

@app.get("/zones/", response_model=List[Zone])
async def list_zones(_: User = Depends(get_current_user)):
    return zones


@app.post("/zones/", response_model=Zone)
async def create_zone(zone: ZoneCreate, _: User = Depends(get_current_user)):
    global next_zone_id
    new_zone = Zone(id=next_zone_id, **zone.model_dump())
    zones.append(new_zone)
    next_zone_id += 1
    return new_zone

@app.post("/vehicles/", response_model=Vehicle)
async def create_vehicle(vehicle: VehicleCreate, user: User = Depends(get_current_user)):
    global next_vehicle_id

    for v in vehicles:
        if v.plate.lower() == vehicle.plate.lower() and v.user_id == user.id:
            raise HTTPException(status_code=409, detail="Vehículo ya registrado")

    new_vehicle = Vehicle(id=next_vehicle_id, user_id=user.id, plate=vehicle.plate)
    vehicles.append(new_vehicle)
    next_vehicle_id += 1
    return new_vehicle


@app.get("/vehicles/", response_model=List[Vehicle])
async def list_vehicles(user: User = Depends(get_current_user)):
    return [v for v in vehicles if v.user_id == user.id]


def find_zone(zone_id: int) -> Zone:
    for z in zones:
        if z.id == zone_id:
            return z
    raise HTTPException(status_code=404, detail="Zona no encontrada")


def find_vehicle_by_plate(user_id: int, plate: str) -> Vehicle:
    for v in vehicles:
        if v.user_id == user_id and v.plate.lower() == plate.lower():
            return v
    raise HTTPException(status_code=404, detail="Vehículo no encontrado")


def find_session_by_id(session_id: int) -> ParkingSession:
    for s in sessions:
        if s.id == session_id:
            return s
    raise HTTPException(status_code=404, detail="Sesión no encontrada")


@app.post("/sessions/start", response_model=ParkingSession)
async def start_session(plate: str, zone_id: int, user: User = Depends(get_current_user)):
    global next_session_id

    vehicle = find_vehicle_by_plate(user.id, plate)

    for s in sessions:
        if s.vehicle_id == vehicle.id and s.status == "active":
            raise HTTPException(status_code=409, detail="Ya existe una sesión activa para esta placa")

    find_zone(zone_id) 

    new_session = ParkingSession(
        id=next_session_id,
        user_id=user.id,
        vehicle_id=vehicle.id,
        zone_id=zone_id,
        started_at=datetime.now(timezone.utc),
        status="active",
        end_at=None,
        minutes=None,
        cost=None,
    )

    sessions.append(new_session)
    next_session_id += 1
    return new_session


@app.post("/sessions/stop/{session_id}", response_model=ParkingSession)
async def stop_session(session_id: int, user: User = Depends(get_current_user)):
    s = find_session_by_id(session_id)

    if s.user_id != user.id:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if s.status != "active":
        raise HTTPException(status_code=422, detail="La sesión no está activa")

    s.ended_at = datetime.now(timezone.utc)
    elapsed_seconds = (s.ended_at - s.started_at).total_seconds()
    s.minutes = ceil(elapsed_seconds / 60)

    zone = find_zone(s.zone_id)

    if s.minutes <= 3:
        base_cost = 0.0
    else:
        base_cost = s.minutes * zone.rate_per_min

    fined = s.minutes > zone.max_minutes
    fine = 100.0 if fined else 0.0
    cost_total = base_cost + fine

    if user.balance < cost_total:
        s.cost = base_cost
        s.status = "pending_payment" if not fined else "fined"
        return s

    user.balance -= cost_total
    s.cost = base_cost
    s.status = "paid" if not fined else "fined"
    return s


@app.get("/sessions/{session_id}")
async def get_session(session_id: int, user: User = Depends(get_current_user)):
    s = find_session_by_id(session_id)
    if s.user_id != user.id:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    zone = find_zone(s.zone_id)
    minutes = s.minutes or 0
    base_cost = 0.0 if minutes <= 3 else minutes * zone.rate_per_min
    fined = minutes > zone.max_minutes
    cost_total = base_cost + (100.0 if fined else 0.0)

    return {
        "id": s.id,
        "minutes": minutes,
        "cost": base_cost,
        "status": s.status,
        "cost_total": cost_total,
        "started_at": s.started_at,
        "ended_at": s.ended_at,
        "vehicle_id": s.vehicle_id,
        "zone_id": s.zone_id,
    }

@app.post("/wallet/deposit")
async def deposit(amount: float, user: User = Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(status_code=422, detail="El depósito debe ser mayor a 0")
    user.balance += amount
    return {"balance": user.balance}

@app.get("/health")
async def health():
    return {"status": "ok"}
