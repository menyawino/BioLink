"""
Bootstrap auth tables and seed default admin user.
Run once on startup or via CLI.
"""

import logging
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.user import UserModel

logger = logging.getLogger(__name__)

DEFAULT_ADMIN = {
    "username": "admin",
    "email": "admin@biolink.local",
    "full_name": "Administrator",
    "role": "admin",
    "scopes": ["admin", "read", "write", "delete"],
}

DEFAULT_USERS = [
    {
        "username": "researcher",
        "email": "researcher@biolink.local",
        "full_name": "Research User",
        "role": "researcher",
        "scopes": ["read", "write"],
        "password": "researcher",
    },
    {
        "username": "viewer",
        "email": "viewer@biolink.local",
        "full_name": "View Only User",
        "role": "viewer",
        "scopes": ["read"],
        "password": "viewer",
    },
]


def ensure_auth_tables():
    """Create users table if it doesn't exist."""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        UserModel.__table__.create(engine)
        logger.info("✓ Created 'users' table")
    else:
        logger.info("✓ 'users' table already exists")


def seed_default_users():
    """Seed default admin and test users (only if they don't exist)."""
    from app.core.security import get_password_hash

    db: Session = SessionLocal()
    try:
        # Seed admin
        existing = db.query(UserModel).filter(UserModel.username == "admin").first()
        if not existing:
            admin = UserModel(
                username=DEFAULT_ADMIN["username"],
                email=DEFAULT_ADMIN["email"],
                full_name=DEFAULT_ADMIN["full_name"],
                role=DEFAULT_ADMIN["role"],
                scopes=DEFAULT_ADMIN["scopes"],
                hashed_password=get_password_hash("admin"),
            )
            db.add(admin)
            logger.info("✓ Seeded default admin user (admin/admin)")

        # Seed test users
        for user_data in DEFAULT_USERS:
            existing = (
                db.query(UserModel)
                .filter(UserModel.username == user_data["username"])
                .first()
            )
            if not existing:
                user = UserModel(
                    username=user_data["username"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    scopes=user_data["scopes"],
                    hashed_password=get_password_hash(user_data["password"]),
                )
                db.add(user)
                logger.info(f"✓ Seeded default user: {user_data['username']}")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed default users: {e}")
    finally:
        db.close()


def bootstrap_auth():
    """Run full auth bootstrap: tables + seed data."""
    ensure_auth_tables()
    seed_default_users()
