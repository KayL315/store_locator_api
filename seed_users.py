from sqlmodel import SQLModel, Session, select

from database import engine
from models import User
from auth import hash_password


def create_user_if_not_exists(
    db: Session,
    user_id: str,
    email: str,
    password: str,
    role: str,
):
    existing_user = db.exec(
        select(User).where(User.email == email)
    ).first()

    if existing_user:
        print(f"User already exists: {email}")
        return

    user = User(
        user_id=user_id,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        status="active",
    )

    db.add(user)
    db.commit()

    print(f"Created user: {email} / role: {role}")


def seed_users():

    with Session(engine) as db:
        create_user_if_not_exists(
            db=db,
            user_id="U001",
            email="admin@test.com",
            password="TestPassword123!",
            role="admin",
        )

        create_user_if_not_exists(
            db=db,
            user_id="U002",
            email="marketer@test.com",
            password="TestPassword123!",
            role="marketer",
        )

        create_user_if_not_exists(
            db=db,
            user_id="U003",
            email="viewer@test.com",
            password="TestPassword123!",
            role="viewer",
        )


if __name__ == "__main__":
    seed_users()