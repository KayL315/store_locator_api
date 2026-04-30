# from sqlmodel import SQLModel, Field, Column, JSON
# from typing import List, Optional
# from datetime import datetime
# import sqlalchemy.dialects.postgresql as pg

# class Store(SQLModel, table=True):
#     __tablename__ = "stores"

#     # Basic Info
#     id: Optional[int] = Field(default=None, primary_key=True)
#     store_id: str = Field(unique=True, index=True, nullable=False)
#     name: str
#     store_type: str
#     status: str = Field(default="active")
#     phone: Optional[str] = None

#     # Coordinates -> 使用 float 保证 6 位以上小数精度
#     latitude: float
#     longitude: float

#     # Address Info
#     address_street: str 
#     address_city: str
#     address_state: str
#     address_postal_code: str
#     address_country: str = Field(default="USA")
    
#     # Services: 存储为数组，方便查询，如果是大项目的话最好写一个单独的services表，manytomany
#     services: List[str] = Field(sa_column=Column(pg.ARRAY(pg.TEXT)))
    
#     # Hours: 存储为 JSONB，方便存储复杂的周一到周日时间 并且后续可以添加假期之类的特殊时间 比较方便不用改数据库结构
#     operating_hours: dict = Field(default={}, sa_column=Column(pg.JSONB))

#     created_at: datetime = Field(default_factory=datetime.utcnow)


# class User(SQLModel, table=True):

#     __tablename__ = "users"

#     id: Optional[int] = Field(default=None, primary_key=True)

#     user_id: str = Field(index=True, unique=True)

#     email: str = Field(index=True, unique=True)

#     hashed_password: str

#     role: str = Field(default="viewer")  # admin, marketer, viewer

#     status: str = Field(default="active")  # active, inactive

#     created_at: datetime = Field(default_factory=datetime.now)

# class RefreshToken(SQLModel, table=True):
#     __tablename__ = "refresh_tokens"

#     id: Optional[int] = Field(default=None, primary_key=True)

#     user_id: str = Field(index=True)

#     token: str = Field(index=True, unique=True)

#     revoked: bool = Field(default=False)

#     expires_at: datetime

#     created_at: datetime = Field(default_factory=datetime.now)

# #暂时不用relationship 因为user不会被硬删除 只会inactive 不需要cascade删除 也不太需要ORM关联 两张表的数据不太需要同时出现在一起 也不需要复杂join

from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship


class StoreService(SQLModel, table=True):
    __tablename__ = "store_services"

    store_id: Optional[int] = Field(
        default=None,
        foreign_key="stores.id",
        primary_key=True
    )
    service_id: Optional[int] = Field(
        default=None,
        foreign_key="services.id",
        primary_key=True
    )


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"

    role_id: Optional[int] = Field(
        default=None,
        foreign_key="roles.id",
        primary_key=True
    )
    permission_id: Optional[int] = Field(
        default=None,
        foreign_key="permissions.id",
        primary_key=True
    )


class Service(SQLModel, table=True):
    __tablename__ = "services"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    stores: List["Store"] = Relationship(
        back_populates="services",
        link_model=StoreService
    )


class Store(SQLModel, table=True):
    __tablename__ = "stores"
    id: Optional[int] = Field(default=None, primary_key=True)

    store_id: str = Field(index=True, unique=True)
    name: str

    store_type: str = Field(index=True)
    status: str = Field(index=True)

    latitude: float = Field(index=True)
    longitude: float = Field(index=True)

    address_street: str
    address_city: str
    address_state: str
    address_postal_code: str = Field(index=True)
    address_country: str

    phone: Optional[str] = None

    operating_hours: dict = Field(
        sa_column=Column(JSONB),
        default_factory=dict
    )

    services: List[Service] = Relationship(
        back_populates="stores",
        link_model=StoreService
    )


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    users: List["User"] = Relationship(back_populates="role")
    permissions: List["Permission"] = Relationship(
        back_populates="roles",
        link_model=RolePermission
    )


class Permission(SQLModel, table=True):
    __tablename__ = "permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    roles: List[Role] = Relationship(
        back_populates="permissions",
        link_model=RolePermission
    )


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str

    role_id: Optional[int] = Field(default=None, foreign_key="roles.id")
    role: Optional[Role] = Relationship(back_populates="users")

    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: str = Field(index=True)
    token_hash: str = Field(index=True, unique=True)

    revoked: bool = Field(default=False)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)