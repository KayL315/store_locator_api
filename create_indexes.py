from sqlalchemy import text
from database import engine


INDEX_SQL = [
    # Composite index for bounding box geo search
    """
    CREATE INDEX IF NOT EXISTS ix_stores_latitude_longitude
    ON stores(latitude, longitude);
    """,

    # Partial index for active stores
    """
    CREATE INDEX IF NOT EXISTS ix_stores_active_status
    ON stores(status)
    WHERE status = 'active';
    """,

    # Store type filtering
    """
    CREATE INDEX IF NOT EXISTS ix_stores_store_type
    ON stores(store_type);
    """,

    # ZIP/postal code lookup
    """
    CREATE INDEX IF NOT EXISTS ix_stores_address_postal_code
    ON stores(address_postal_code);
    """,

    # User login lookup
    """
    CREATE INDEX IF NOT EXISTS ix_users_email
    ON users(email);
    """,

    # Refresh token lookup
    """
    CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_hash
    ON refresh_tokens(token_hash);
    """,

    # Optional but useful: service name lookup
    """
    CREATE INDEX IF NOT EXISTS ix_services_name
    ON services(name);
    """,

    # Optional but useful: role name lookup
    """
    CREATE INDEX IF NOT EXISTS ix_roles_name
    ON roles(name);
    """,

    # Optional but useful: permission name lookup
    """
    CREATE INDEX IF NOT EXISTS ix_permissions_name
    ON permissions(name);
    """,
]


def create_indexes():
    with engine.begin() as conn:
        for sql in INDEX_SQL:
            conn.execute(text(sql))

    print("Indexes created successfully.")


if __name__ == "__main__":
    create_indexes()