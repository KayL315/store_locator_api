from sqlmodel import SQLModel, Field, Column, JSON
from typing import List, Optional
from datetime import datetime
import sqlalchemy.dialects.postgresql as pg

class Store(SQLModel, table=True):
    __tablename__ = "stores"

    # Basic Info
    id: Optional[int] = Field(default=None, primary_key=True)
    store_id: str = Field(unique=True, index=True, nullable=False)
    name: str
    store_type: str
    status: str = Field(default="active")
    phone: Optional[str] = None

    # Coordinates -> 使用 float 保证 6 位以上小数精度
    latitude: float
    longitude: float

    # Address Info
    address_street: str 
    address_city: str
    address_state: str
    address_postal_code: str
    address_country: str = Field(default="USA")
    
    # Services: 存储为数组，方便查询
    services: List[str] = Field(sa_column=Column(pg.ARRAY(pg.TEXT)))
    
    # Hours: 存储为 JSONB，方便存储复杂的周一到周日时间 并且后续可以添加假期之类的特殊时间 比较方便不用改数据库结构
    operating_hours: dict = Field(default={}, sa_column=Column(pg.JSONB))

    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: str = Field(index=True, unique=True)

    email: str = Field(index=True, unique=True)

    hashed_password: str

    role: str = Field(default="viewer")  # admin, marketer, viewer

    status: str = Field(default="active")  # active, inactive

    created_at: datetime = Field(default_factory=datetime.utcnow)

class RefreshToken(SQLModel, table=True):

    __tablename__ = "refresh_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: str = Field(index=True)

    token: str = Field(index=True, unique=True)

    revoked: bool = Field(default=False)

    expires_at: datetime

    created_at: datetime = Field(default_factory=datetime.utcnow)