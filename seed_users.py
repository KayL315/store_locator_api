from sqlmodel import Session, select
from models import User, RefreshToken
from database import engine
from models import User, Role, Permission
from auth import hash_password


DEFAULT_PASSWORD = "TestPassword123!"


ROLE_PERMISSIONS = {
    "admin": [
        "store:read",
        "store:create",
        "store:update",
        "store:delete",
        "store:import",
        "user:create",
        "user:read",
        "user:update",
        "user:delete",
    ],
    "marketer": [
        "store:read",
        "store:create",
        "store:update",
        "store:delete",
        "store:import",
    ],
    "viewer": [
        "store:read",
    ],
}


SEED_USERS = [
    {
        "user_id": "U001",
        "email": "admin@test.com",
        "role": "admin",
    },
    {
        "user_id": "U002",
        "email": "marketer@test.com",
        "role": "marketer",
    },
    {
        "user_id": "U003",
        "email": "viewer@test.com",
        "role": "viewer",
    },
]
def reset_admin_for_tests():
    seed_users()

    with Session(engine) as db:
        admin = db.exec(
            select(User).where(User.email == "admin@test.com")
        ).first()

        assert admin is not None

        admin.hashed_password = hash_password("TestPassword123!")
        admin.must_change_password = False
        admin.status = "active"

        old_tokens = db.exec(
            select(RefreshToken).where(RefreshToken.user_id == admin.user_id)
        ).all()

        for token in old_tokens:
            db.delete(token)

        db.add(admin)
        db.commit()

def get_or_create_permission(db: Session, permission_name: str) -> Permission:
    permission = db.exec(
        select(Permission).where(Permission.name == permission_name)
    ).first()

    if permission:
        return permission

    permission = Permission(name=permission_name)
    db.add(permission)
    db.commit()
    db.refresh(permission)

    print(f"Created permission: {permission_name}")
    return permission


def get_or_create_role(db: Session, role_name: str) -> Role:
    role = db.exec(
        select(Role).where(Role.name == role_name)
    ).first()

    if role:
        return role

    role = Role(name=role_name)
    db.add(role)
    db.commit()
    db.refresh(role)

    print(f"Created role: {role_name}")
    return role


def seed_roles_and_permissions(db: Session):
    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role = get_or_create_role(db, role_name)

        for permission_name in permission_names:
            permission = get_or_create_permission(db, permission_name)

            existing_permission_names = {p.name for p in role.permissions}

            if permission.name not in existing_permission_names:
                role.permissions.append(permission)

        db.add(role)
        db.commit()
        db.refresh(role)

        print(f"Seeded permissions for role: {role_name}")


def create_user_if_not_exists(
    db: Session,
    user_id: str,
    email: str,
    role_name: str,
):
    existing_user = db.exec(
        select(User).where(User.email == email)
    ).first()

    if existing_user:
        print(f"User already exists: {email}")
        return

    role = db.exec(
        select(Role).where(Role.name == role_name)
    ).first()

    if not role:
        raise ValueError(f"Role not found: {role_name}")

    user = User(
        user_id=user_id,
        email=email,
        hashed_password=hash_password(DEFAULT_PASSWORD),
        role_id=role.id,
        status="active",
        must_change_password=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    print(f"Created user: {email} / role: {role_name}")


def seed_users():
    with Session(engine) as db:
        seed_roles_and_permissions(db)

        for user_data in SEED_USERS:
            create_user_if_not_exists(
                db=db,
                user_id=user_data["user_id"],
                email=user_data["email"],
                role_name=user_data["role"],
            )


if __name__ == "__main__":
    seed_users()