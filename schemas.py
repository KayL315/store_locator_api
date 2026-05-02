from typing import List, Optional, Dict
from pydantic import BaseModel, Field, model_validator, EmailStr, ConfigDict
from enum import Enum

class StoreStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    temporarily_closed = "temporarily_closed"

class StoreSearchRequest(BaseModel):
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lon: Optional[float] = Field(default=None, ge=-180, le=180)
    address: Optional[str] = None
    postal_code: Optional[str] = None

    radius_miles: float = Field(default=10.0, gt=0, le=100)

    services: Optional[List[str]] = None

    store_types: Optional[List[str]] = None

    open_now: bool = False

    @model_validator(mode="after")
    def validate_search_input(self):
        has_coordinates = self.lat is not None and self.lon is not None
        has_address = bool(self.address)
        has_postal_code = bool(self.postal_code)

        if not has_coordinates and not has_address and not has_postal_code:
            raise ValueError("Provide either lat/lon, address, or postal_code.")

        if (self.lat is None) != (self.lon is None):
            raise ValueError("lat and lon must be provided together.")

        return self


class StoreResponse(BaseModel):
    store_id: str
    name: str
    store_type: str
    status: StoreStatus
    phone: Optional[str] = None

    latitude: float
    longitude: float

    address_street: str
    address_city: str
    address_state: str
    address_postal_code: str
    address_country: str

    services: List[str]
    operating_hours: Dict[str, str]

    distance_miles: float
    is_open_now: bool


class StoreSearchMetadata(BaseModel):
    searched_location: Dict[str, float]
    radius_miles: float
    services: Optional[List[str]]
    store_types: Optional[List[str]]
    open_now: bool
    total_found: int


class StoreSearchResponse(BaseModel):
    metadata: StoreSearchMetadata
    stores: List[StoreResponse]


class LoginRequest(BaseModel):

    email: EmailStr

    password: str

class TokenResponse(BaseModel):

    access_token: str

    refresh_token: str

    token_type: str = "bearer"

class RefreshRequest(BaseModel):

    refresh_token: str

class LogoutRequest(BaseModel):

    refresh_token: str

class UserResponse(BaseModel):

    user_id: str

    email: str

    role: str

    status: str


class StoreCreate(BaseModel):

    store_id: str

    name: str

    store_type: str

    status: StoreStatus = StoreStatus.active

    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)

    address_street: str

    address_city: str

    address_state: str

    address_postal_code: str

    address_country: str = "USA"

    phone: Optional[str] = None

    services: List[str] = []

    operating_hours: Dict[str, str]

class StoreUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = None

    phone: Optional[str] = None

    services: Optional[List[str]] = None

    status: Optional[StoreStatus] = None

    operating_hours: Optional[Dict[str, str]] = None

class UserCreate(BaseModel):
    user_id: str
    email: EmailStr
    password: str
    role: str = "viewer"
    status: str = "active"


class UserUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    email: EmailStr
    current_password: str
    new_password: str