import pandas as pd
from sqlmodel import Session, SQLModel, select

from database import engine
from models import Store, Service
from csv_validation import validate_csv_headers, validate_store_row, REQUIRED_COLUMNS


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_or_create_services(db: Session, service_names: list[str]) -> list[Service]:
    services = []

    for name in service_names:
        service = db.exec(select(Service).where(Service.name == name)).first()

        if not service:
            service = Service(name=name)
            db.add(service)
            db.flush()

        services.append(service)

    return services


def transform_row(row: dict, db: Session) -> Store:
    validate_store_row(row)

    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    hours_dict = {day: row[f"hours_{day}"] for day in days}

    service_names = row["services"].split("|") if row["services"] else []
    service_objects = get_or_create_services(db, service_names)

    store = Store(
        store_id=row["store_id"],
        name=row["name"],
        store_type=row["store_type"],
        status=row["status"],
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        address_street=row["address_street"],
        address_city=row["address_city"],
        address_state=row["address_state"],
        address_postal_code=str(row["address_postal_code"]).zfill(5),
        address_country=row["address_country"],
        phone=str(row["phone"]),
        operating_hours=hours_dict,
    )

    store.services = service_objects
    return store


def import_csv_to_db(file_path: str):
    print(f"开始从 {file_path} 导入数据")

    df = pd.read_csv(file_path, dtype=str).fillna("")

    headers = list(df.columns)
    validate_csv_headers(headers)

    with Session(engine) as session:
        try:
            created = 0
            updated = 0

            for idx, row in df.iterrows():
                row_dict = row.to_dict()

                store_id = row_dict["store_id"]

                existing_store = session.exec(
                    select(Store).where(Store.store_id == store_id)
                ).first()

                new_store_data = transform_row(row_dict, session)

                if existing_store:
                    existing_store.name = new_store_data.name
                    existing_store.store_type = new_store_data.store_type
                    existing_store.status = new_store_data.status
                    existing_store.latitude = new_store_data.latitude
                    existing_store.longitude = new_store_data.longitude
                    existing_store.address_street = new_store_data.address_street
                    existing_store.address_city = new_store_data.address_city
                    existing_store.address_state = new_store_data.address_state
                    existing_store.address_postal_code = new_store_data.address_postal_code
                    existing_store.address_country = new_store_data.address_country
                    existing_store.phone = new_store_data.phone
                    existing_store.operating_hours = new_store_data.operating_hours
                    existing_store.services = new_store_data.services

                    session.add(existing_store)
                    updated += 1
                else:
                    session.add(new_store_data)
                    created += 1

            session.commit()

            print("导入成功")
            print(f"Created: {created}")
            print(f"Updated: {updated}")
            print(f"Total processed: {created + updated}")

        except Exception as e:
            session.rollback()
            print(f"导入失败，已回滚：{e}")


if __name__ == "__main__":
    create_db_and_tables()
    import_csv_to_db("stores_1000.csv")