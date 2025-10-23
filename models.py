from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    api_key: str
    balance: float = 300.0
    vehicles: List["Vehicle"] = Relationship(back_populates="user")
    sessions: List["ParkingSession"] = Relationship(back_populates="user")


class Zone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    rate_per_min: float
    max_minutes: int
    sessions: List["ParkingSession"] = Relationship(back_populates="zone")


class Vehicle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    plate: str
    user: Optional[User] = Relationship(back_populates="vehicles")
    sessions: List["ParkingSession"] = Relationship(back_populates="vehicle")


class ParkingSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    vehicle_id: int = Field(foreign_key="vehicle.id")
    zone_id: int = Field(foreign_key="zone.id")
    started_at: datetime
    ended_at: Optional[datetime] = None
    minutes: Optional[int] = None
    cost: Optional[float] = None
    status: str = "active"

    user: Optional[User] = Relationship(back_populates="sessions")
    vehicle: Optional[Vehicle] = Relationship(back_populates="sessions")
    zone: Optional[Zone] = Relationship(back_populates="sessions")



class ZoneCreate(SQLModel):
    name: str
    rate_per_min: float
    max_minutes: int


class VehicleCreate(SQLModel):
    plate: str
