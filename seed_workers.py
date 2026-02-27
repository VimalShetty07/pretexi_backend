"""
Seed realistic worker/employee data into the database.
Run from backend dir: python seed_workers.py
Requires: organisation + mock users already seeded (run seed_mock_users.py first).
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.database import SessionLocal
from app.models.models import Organisation, Worker, WorkerStatus, WorkerStage, RiskLevel

MOCK_LICENCE = "DEMO-LICENCE-001"

WORKERS = [
    {
        "name": "Sarah Johnson",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "email": "sarah.johnson@protexi.local",
        "phone": "+44 7700 100001",
        "nationality": "Indian",
        "job_title": "Senior Software Engineer",
        "department": "Engineering",
        "soc_code": "2136",
        "salary": 55000,
        "route": "Skilled Worker",
        "work_location": "London HQ",
        "is_hybrid": True,
        "status": WorkerStatus.ACTIVE,
        "stage": WorkerStage.ACTIVE_SPONSORSHIP,
        "risk_level": RiskLevel.LOW,
        "start_date": datetime(2023, 3, 15, tzinfo=timezone.utc),
        "visa_expiry": datetime(2026, 9, 14, tzinfo=timezone.utc),
        "passport_expiry": datetime(2028, 6, 20, tzinfo=timezone.utc),
        "brp_expiry": datetime(2026, 9, 14, tzinfo=timezone.utc),
        "date_of_birth": datetime(1992, 5, 12, tzinfo=timezone.utc),
        "gender": "Female",
        "place_of_birth": "Mumbai",
        "country_of_birth": "India",
        "address": "45 Baker Street, London",
        "postal_code": "W1U 8EW",
        "ni_number": "AB123456C",
        "passport_number": "P1234567",
        "passport_place_of_issue": "Mumbai",
        "passport_issue_date": datetime(2023, 6, 20, tzinfo=timezone.utc),
        "emergency_contact_name": "Vikram Johnson",
        "emergency_contact_phone": "+44 7700 200001",
        "next_of_kin_name": "Vikram Johnson",
        "next_of_kin_phone": "+44 7700 200001",
        "employee_id": "EMP001",
        "employee_type": "migrant",
    },
    {
        "name": "Raj Patel",
        "email": "raj.patel@protexi.local",
        "phone": "+44 7700 100002",
        "nationality": "Indian",
        "job_title": "Data Analyst",
        "department": "Analytics",
        "soc_code": "2425",
        "salary": 38000,
        "route": "Skilled Worker",
        "work_location": "Manchester Office",
        "is_hybrid": False,
        "status": WorkerStatus.ACTIVE,
        "stage": WorkerStage.ACTIVE_SPONSORSHIP,
        "risk_level": RiskLevel.MEDIUM,
        "start_date": datetime(2024, 1, 8, tzinfo=timezone.utc),
        "visa_expiry": datetime(2026, 5, 10, tzinfo=timezone.utc),
        "passport_expiry": datetime(2027, 11, 3, tzinfo=timezone.utc),
        "brp_expiry": datetime(2026, 5, 10, tzinfo=timezone.utc),
    },
    {
        "name": "Maria Garcia",
        "email": "maria.garcia@protexi.local",
        "phone": "+44 7700 100003",
        "nationality": "Spanish",
        "job_title": "Marketing Manager",
        "department": "Marketing",
        "soc_code": "1132",
        "salary": 45000,
        "route": "Skilled Worker",
        "work_location": "London HQ",
        "is_hybrid": True,
        "status": WorkerStatus.ACTIVE,
        "stage": WorkerStage.ACTIVE_SPONSORSHIP,
        "risk_level": RiskLevel.HIGH,
        "start_date": datetime(2022, 11, 1, tzinfo=timezone.utc),
        "visa_expiry": datetime(2026, 3, 15, tzinfo=timezone.utc),
        "passport_expiry": datetime(2029, 2, 10, tzinfo=timezone.utc),
        "brp_expiry": datetime(2026, 3, 15, tzinfo=timezone.utc),
    },
    {
        "name": "Li Wei",
        "email": "li.wei@protexi.local",
        "phone": "+44 7700 100004",
        "nationality": "Chinese",
        "job_title": "Financial Controller",
        "department": "Finance",
        "soc_code": "2421",
        "salary": 62000,
        "route": "Skilled Worker",
        "work_location": "London HQ",
        "is_hybrid": False,
        "status": WorkerStatus.ACTIVE,
        "stage": WorkerStage.ACTIVE_SPONSORSHIP,
        "risk_level": RiskLevel.LOW,
        "start_date": datetime(2023, 7, 10, tzinfo=timezone.utc),
        "visa_expiry": datetime(2027, 7, 9, tzinfo=timezone.utc),
        "passport_expiry": datetime(2030, 1, 15, tzinfo=timezone.utc),
        "brp_expiry": datetime(2027, 7, 9, tzinfo=timezone.utc),
    },
    {
        "name": "Priya Sharma",
        "email": "priya.sharma@protexi.local",
        "phone": "+44 7700 100005",
        "nationality": "Indian",
        "job_title": "UX Designer",
        "department": "Design",
        "soc_code": "2142",
        "salary": 42000,
        "route": "Skilled Worker",
        "work_location": "London HQ",
        "is_remote": True,
        "status": WorkerStatus.ACTIVE,
        "stage": WorkerStage.ACTIVE_SPONSORSHIP,
        "risk_level": RiskLevel.LOW,
        "start_date": datetime(2024, 4, 1, tzinfo=timezone.utc),
        "visa_expiry": datetime(2028, 3, 31, tzinfo=timezone.utc),
        "passport_expiry": datetime(2031, 8, 5, tzinfo=timezone.utc),
        "brp_expiry": datetime(2028, 3, 31, tzinfo=timezone.utc),
    },
    {
        "name": "Ahmed Hassan",
        "email": "ahmed.hassan@protexi.local",
        "phone": "+44 7700 100006",
        "nationality": "Egyptian",
        "job_title": "DevOps Engineer",
        "department": "Engineering",
        "soc_code": "2136",
        "salary": 52000,
        "route": "Skilled Worker",
        "work_location": "Manchester Office",
        "is_hybrid": True,
        "status": WorkerStatus.ACTIVE,
        "stage": WorkerStage.ACTIVE_SPONSORSHIP,
        "risk_level": RiskLevel.MEDIUM,
        "start_date": datetime(2023, 9, 18, tzinfo=timezone.utc),
        "visa_expiry": datetime(2026, 9, 17, tzinfo=timezone.utc),
        "passport_expiry": datetime(2028, 4, 22, tzinfo=timezone.utc),
        "brp_expiry": datetime(2026, 9, 17, tzinfo=timezone.utc),
    },
    {
        "name": "Yuki Tanaka",
        "email": "yuki.tanaka@protexi.local",
        "phone": "+44 7700 100007",
        "nationality": "Japanese",
        "job_title": "Product Manager",
        "department": "Product",
        "soc_code": "2133",
        "salary": 58000,
        "route": "Skilled Worker",
        "work_location": "London HQ",
        "is_hybrid": True,
        "status": WorkerStatus.ACTIVE,
        "stage": WorkerStage.ACTIVE_SPONSORSHIP,
        "risk_level": RiskLevel.LOW,
        "start_date": datetime(2024, 2, 12, tzinfo=timezone.utc),
        "visa_expiry": datetime(2028, 2, 11, tzinfo=timezone.utc),
        "passport_expiry": datetime(2032, 10, 8, tzinfo=timezone.utc),
        "brp_expiry": datetime(2028, 2, 11, tzinfo=timezone.utc),
    },
    {
        "name": "Oluwaseun Adeyemi",
        "email": "seun.adeyemi@protexi.local",
        "phone": "+44 7700 100008",
        "nationality": "Nigerian",
        "job_title": "QA Engineer",
        "department": "Engineering",
        "soc_code": "2136",
        "salary": 40000,
        "route": "Skilled Worker",
        "work_location": "Manchester Office",
        "is_hybrid": False,
        "status": WorkerStatus.ACTIVE,
        "stage": WorkerStage.PRE_START,
        "risk_level": RiskLevel.LOW,
        "start_date": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "visa_expiry": datetime(2029, 2, 28, tzinfo=timezone.utc),
        "passport_expiry": datetime(2031, 5, 14, tzinfo=timezone.utc),
        "brp_expiry": datetime(2029, 2, 28, tzinfo=timezone.utc),
    },
    {
        "name": "Elena Popova",
        "email": "elena.popova@protexi.local",
        "phone": "+44 7700 100009",
        "nationality": "Russian",
        "job_title": "HR Business Partner",
        "department": "People",
        "soc_code": "1135",
        "salary": 48000,
        "route": "Skilled Worker",
        "work_location": "London HQ",
        "is_hybrid": True,
        "status": WorkerStatus.SUSPENDED,
        "stage": WorkerStage.ACTIVE_SPONSORSHIP,
        "risk_level": RiskLevel.CRITICAL,
        "start_date": datetime(2022, 6, 20, tzinfo=timezone.utc),
        "visa_expiry": datetime(2026, 6, 19, tzinfo=timezone.utc),
        "passport_expiry": datetime(2027, 9, 30, tzinfo=timezone.utc),
        "brp_expiry": datetime(2026, 6, 19, tzinfo=timezone.utc),
    },
    {
        "name": "Carlos Mendes",
        "email": "carlos.mendes@protexi.local",
        "phone": "+44 7700 100010",
        "nationality": "Brazilian",
        "job_title": "Business Analyst",
        "department": "Operations",
        "soc_code": "2423",
        "salary": 44000,
        "route": "Skilled Worker",
        "work_location": "London HQ",
        "is_hybrid": False,
        "status": WorkerStatus.TERMINATED,
        "stage": WorkerStage.TERMINATED,
        "risk_level": RiskLevel.LOW,
        "start_date": datetime(2021, 4, 5, tzinfo=timezone.utc),
        "termination_date": datetime(2025, 12, 31, tzinfo=timezone.utc),
        "visa_expiry": datetime(2026, 4, 4, tzinfo=timezone.utc),
        "passport_expiry": datetime(2028, 7, 12, tzinfo=timezone.utc),
        "brp_expiry": datetime(2026, 4, 4, tzinfo=timezone.utc),
    },
]


def main():
    db = SessionLocal()
    try:
        org = db.query(Organisation).filter(Organisation.licence_number == MOCK_LICENCE).first()
        if not org:
            print("ERROR: Organisation not found. Run seed_mock_users.py first.")
            return

        print(f"Seeding workers for: {org.name}")

        for w in WORKERS:
            existing = db.query(Worker).filter(
                Worker.email == w["email"],
                Worker.organisation_id == org.id,
            ).first()
            if existing:
                print(f"  Already exists: {w['name']}")
                continue

            worker = Worker(organisation_id=org.id, **w)
            db.add(worker)
            print(f"  Created: {w['name']} — {w['job_title']} ({w['status'].value})")

        db.commit()
        count = db.query(Worker).filter(Worker.organisation_id == org.id).count()
        print(f"Done. Total workers in org: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
