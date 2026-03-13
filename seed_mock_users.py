"""
Seed platform owner + demo organisation users for development.
Run from backend dir: python seed_mock_users.py
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bcrypt
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.models import Organisation, User, UserRole

settings = get_settings()

PLATFORM_ORG_NAME = "Protexi Platform"
PLATFORM_ORG_LICENCE = "PLATFORM-ROOT-001"
DEMO_ORG_NAME = "Protexi Demo Ltd"
DEMO_ORG_LICENCE = "DEMO-LICENCE-001"
MOCK_PASSWORD = settings.MOCK_SEED_PASSWORD
PLATFORM_OWNER_PASSWORD = settings.PLATFORM_OWNER_PASSWORD or settings.MOCK_SEED_PASSWORD

MOCK_USERS = [
    {"email": "admin@protexi.local", "full_name": "Mock Admin", "role": UserRole.SUPER_ADMIN},
    {"email": "hr@protexi.local", "full_name": "Mock HR Officer", "role": UserRole.HR_OFFICER},
    {"email": "employee@protexi.local", "full_name": "Mock Employee", "role": UserRole.EMPLOYEE},
]


def _get_or_create_org(db, name: str, licence_number: str, slug: str):
    org = db.query(Organisation).filter(Organisation.licence_number == licence_number).first()
    if not org:
        org = Organisation(
            name=name,
            licence_number=licence_number,
            slug=slug,
            portal_plan="enterprise" if "platform" in slug else "starter_monthly",
            is_active=True,
        )
        db.add(org)
        db.flush()
        print(f"Created organisation: {org.name} ({org.licence_number})")
    else:
        print(f"Using existing organisation: {org.name}")
    return org


def _ensure_user(db, organisation_id: str, email: str, full_name: str, role: UserRole, password: str):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"  User already exists: {email}")
        return existing

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(
        organisation_id=organisation_id,
        email=email,
        hashed_password=hashed,
        full_name=full_name,
        role=role,
        must_reset_password=False,
    )
    db.add(user)
    print(f"  Created user: {email} ({role.value})")
    return user


def main():
    db = SessionLocal()
    try:
        platform_org = _get_or_create_org(
            db=db,
            name=PLATFORM_ORG_NAME,
            licence_number=PLATFORM_ORG_LICENCE,
            slug="platform",
        )
        demo_org = _get_or_create_org(
            db=db,
            name=DEMO_ORG_NAME,
            licence_number=DEMO_ORG_LICENCE,
            slug="demo",
        )

        _ensure_user(
            db=db,
            organisation_id=platform_org.id,
            email=settings.PLATFORM_OWNER_EMAIL,
            full_name=settings.PLATFORM_OWNER_NAME,
            role=UserRole.PLATFORM_OWNER,
            password=PLATFORM_OWNER_PASSWORD,
        )

        for user_data in MOCK_USERS:
            _ensure_user(
                db=db,
                organisation_id=demo_org.id,
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                password=MOCK_PASSWORD,
            )

        db.commit()
        print(
            "Done.\n"
            f"Platform owner: {settings.PLATFORM_OWNER_EMAIL}\n"
            "Mock users: admin@protexi.local, hr@protexi.local, employee@protexi.local"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
