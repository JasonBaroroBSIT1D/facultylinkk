"""Seed isolated QA faculty + reviewer on facultylink_qa only."""

from __future__ import annotations

import json
import os
import secrets
import sys

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


def _qa_password() -> str:
    pwd = (os.environ.get("QA_ACCOUNT_PASSWORD") or os.environ.get("QA_PASSWORD") or "").strip()
    if pwd:
        return pwd
    generated = secrets.token_urlsafe(18)
    print(
        "QA_ACCOUNT_PASSWORD was not set; generated a one-time password for this run only. "
        "Set QA_ACCOUNT_PASSWORD in your local .env (never commit) and re-seed to fix login.",
        file=sys.stderr,
    )
    return generated


def main() -> int:
    qa_url = (os.environ.get("FACULTYLINK_QA_DATABASE_URL") or "").strip()
    if not qa_url:
        print("Set FACULTYLINK_QA_DATABASE_URL before seeding QA accounts.", file=sys.stderr)
        return 2
    os.environ["DATABASE_URL"] = qa_url
    os.environ["FACULTYLINK_QA_DATABASE_ALLOWED"] = "1"
    from scripts.qa_db_guard import require_qa_test_database

    require_qa_test_database()

    faculty_email = (os.environ.get("QA_FACULTY_EMAIL") or "qa-kra4-faculty@facultylink.test").strip()
    reviewer_email = (os.environ.get("QA_REVIEWER_EMAIL") or "qa-kra4-reviewer@facultylink.test").strip()
    password = _qa_password()

    from config import Config
    from factory import create_app
    from models import FacultyProfile, User, new_public_id
    from auth.permissions import ROLE_ADMINISTRATOR, ROLE_FACULTY, ROLE_REVIEWER
    from extensions import db

    app = create_app(Config)
    with app.app_context():
        reviewer = User.query.filter_by(email=reviewer_email).first()
        if not reviewer:
            reviewer = User(
                email=reviewer_email,
                role=ROLE_REVIEWER,
                full_name="KRA IV QA Reviewer",
                office="QA",
                is_active=True,
                must_change_password=False,
                public_id=new_public_id("usr_"),
            )
            db.session.add(reviewer)
            db.session.flush()
        reviewer.set_password(password)

        faculty = User.query.filter_by(email=faculty_email).first()
        if not faculty:
            faculty = User(
                email=faculty_email,
                role=ROLE_FACULTY,
                full_name="KRA IV QA Faculty",
                is_active=True,
                must_change_password=False,
                public_id=new_public_id("usr_"),
            )
            db.session.add(faculty)
            db.session.flush()

            profile = FacultyProfile(
                user_id=faculty.id,
                employee_no="QA-KRA4-001",
                current_rank="Assistant Professor I",
                department="QA Department",
                college="QA College",
                reviewer_user_id=reviewer.id,
                public_id=new_public_id("fac_"),
            )
            db.session.add(profile)
        else:
            profile = FacultyProfile.query.filter_by(user_id=faculty.id).first()
            if profile and profile.reviewer_user_id != reviewer.id:
                profile.reviewer_user_id = reviewer.id
        faculty.set_password(password)

        admin_email = (os.environ.get("QA_ADMIN_EMAIL") or "qa-kra4-admin@facultylink.test").strip()
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                role=ROLE_ADMINISTRATOR,
                full_name="KRA IV QA Admin",
                is_active=True,
                must_change_password=False,
                public_id=new_public_id("usr_"),
            )
            admin.set_password(password)
            db.session.add(admin)
        else:
            admin.set_password(password)

        db.session.commit()
        profile = FacultyProfile.query.filter_by(user_id=faculty.id).first()
        print(
            json.dumps(
                {
                    "facultyEmail": faculty_email,
                    "reviewerEmail": reviewer_email,
                    "adminEmail": admin_email,
                    "facultyPublicId": profile.public_id if profile else None,
                    "passwordConfigured": bool(os.environ.get("QA_ACCOUNT_PASSWORD") or os.environ.get("QA_PASSWORD")),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
