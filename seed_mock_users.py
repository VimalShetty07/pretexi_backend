"""
Seed one organisation and 3 mock users (admin, hr, employee) for development.
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

MOCK_ORG_NAME = "Protexi Demo Ltd"
MOCK_LICENCE = "DEMO-LICENCE-001"
settings = get_settings()
MOCK_PASSWORD = settings.MOCK_SEED_PASSWORD

MOCK_USERS = [
    {
        "email": "admin@protexi.local",
        "full_name": "Mock Admin",
        "role": UserRole.SUPER_ADMIN,
    },
    {
        "email": "hr@protexi.local",
        "full_name": "Mock HR Officer",
        "role": UserRole.HR_OFFICER,
    },
    {
        "email": "employee@protexi.local",
        "full_name": "Mock Employee",
        "role": UserRole.EMPLOYEE,
    },
]


def main():
    db = SessionLocal()
    try:
        org = db.query(Organisation).filter(Organisation.licence_number == MOCK_LICENCE).first()
        if not org:
            org = Organisation(name=MOCK_ORG_NAME, licence_number=MOCK_LICENCE)
            db.add(org)
            db.flush()
            print(f"Created organisation: {org.name} ({org.licence_number})")
        else:
            print(f"Using existing organisation: {org.name}")

        hashed = bcrypt.hashpw(MOCK_PASSWORD.encode(), bcrypt.gensalt()).decode()
        for u in MOCK_USERS:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    organisation_id=org.id,
                    email=u["email"],
                    hashed_password=hashed,
                    full_name=u["full_name"],
                    role=u["role"],
                )
                db.add(user)
                print(f"  Created user: {u['email']} ({u['role'].value})")
            else:
                print(f"  User already exists: {u['email']}")

        db.commit()
        print("Done. Mock users: admin@protexi.local, hr@protexi.local, employee@protexi.local")
    finally:
        db.close()


if __name__ == "__main__":
    main()
