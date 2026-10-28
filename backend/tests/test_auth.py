from unittest.mock import patch

import pytest

pytestmark = pytest.mark.skip(
    reason=(
        "PostgreSQL integration tests are disabled while using a single application "
        "database (facultylink). Re-enable after an isolated test database or in-memory "
        "strategy is configured."
    )
)

from extensions import db
from models import FacultyProfile, User


def _create_user(*, email, role, password="SecurePass1", must_change=False, with_profile=False):
    user = User(
        email=email,
        role=role,
        full_name=f"Test {role}",
        is_active=True,
        must_change_password=must_change,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    if with_profile:
        db.session.add(
            FacultyProfile(
                user_id=user.id,
                employee_no=f"EMP-{user.id}",
                current_rank="Instructor I",
                department="Education",
                college="Education",
                campus="Main Campus",
            )
        )
    db.session.commit()
    return user


def _login(client, identity, password, client_channel=None):
    body = {"email": identity, "password": password}
    if client_channel:
        body["client"] = client_channel
    return client.post("/api/auth/login", json=body)


def test_login_and_session(client):
    _create_user(email="admin@test.edu", role="administrator", password="AdminPass1")
    response = _login(client, "admin@test.edu", "AdminPass1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["session"]["role"] == "administrator"
    assert data["accessToken"]

    session = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {data['accessToken']}"},
    )
    assert session.status_code == 200
    assert session.get_json()["user"]["email"] == "admin@test.edu"


def test_web_blocks_faculty(client):
    _create_user(email="faculty@test.edu", role="faculty", password="FacultyPass1", with_profile=True)
    response = _login(client, "faculty@test.edu", "FacultyPass1", client_channel="web")
    assert response.status_code == 403


def test_mobile_blocks_administrator(client):
    _create_user(email="admin@test.edu", role="administrator", password="AdminPass1")
    response = _login(client, "admin@test.edu", "AdminPass1", client_channel="mobile")
    assert response.status_code == 403


def test_role_probes(client):
    admin = _create_user(email="admin@test.edu", role="administrator", password="AdminPass1")
    reviewer = _create_user(email="rev@test.edu", role="reviewer", password="ReviewerPass1")
    faculty = _create_user(
        email="fac@test.edu", role="faculty", password="FacultyPass1", with_profile=True
    )

    admin_token = _login(client, admin.email, "AdminPass1").get_json()["accessToken"]
    reviewer_token = _login(client, reviewer.email, "ReviewerPass1").get_json()["accessToken"]
    faculty_token = _login(client, faculty.email, "FacultyPass1").get_json()["accessToken"]

    assert client.get("/api/auth/probe/administrator", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200
    assert client.get("/api/auth/probe/administrator", headers={"Authorization": f"Bearer {reviewer_token}"}).status_code == 403
    assert client.get("/api/auth/probe/reviewer", headers={"Authorization": f"Bearer {reviewer_token}"}).status_code == 200
    assert client.get("/api/auth/probe/faculty", headers={"Authorization": f"Bearer {faculty_token}"}).status_code == 200


def test_faculty_login_must_change_password(client):
    faculty = _create_user(
        email="new.faculty@test.edu",
        role="faculty",
        password="TempPass1",
        must_change=True,
        with_profile=True,
    )
    response = client.post(
        "/api/auth/login",
        json={"email": faculty.email, "password": "TempPass1", "client": "mobile"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["session"]["mustChangePassword"] is True
    assert payload["user"]["mustChangePassword"] is True
    token = payload["accessToken"]
    blocked = client.get(
        "/api/faculty/me/reviewer",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert blocked.status_code == 403
    assert blocked.get_json()["code"] == "PASSWORD_CHANGE_REQUIRED"

    changed = client.post(
        "/api/auth/change-password",
        json={"currentPassword": "TempPass1", "newPassword": "NewFaculty1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert changed.status_code == 200
    assert changed.get_json()["session"]["mustChangePassword"] is False
    assert client.post(
        "/api/auth/login",
        json={"email": faculty.email, "password": "TempPass1", "client": "mobile"},
    ).status_code == 401
    assert client.post(
        "/api/auth/login",
        json={"email": faculty.email, "password": "NewFaculty1", "client": "mobile"},
    ).status_code == 200


def test_change_password(client):
    _create_user(email="admin@test.edu", role="administrator", password="AdminPass1", must_change=True)
    token = _login(client, "admin@test.edu", "AdminPass1").get_json()["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}
    bad = client.post(
        "/api/auth/change-password",
        json={"currentPassword": "wrong", "newPassword": "NewAdminPass1"},
        headers=headers,
    )
    assert bad.status_code == 400

    ok = client.post(
        "/api/auth/change-password",
        json={"currentPassword": "AdminPass1", "newPassword": "NewAdminPass1"},
        headers=headers,
    )
    assert ok.status_code == 200
    assert _login(client, "admin@test.edu", "NewAdminPass1").status_code == 200


@patch("auth.services._generate_otp", return_value="654321")
def test_password_reset_flow(mock_otp, client):
    _create_user(email="faculty@test.edu", role="faculty", password="FacultyPass1", with_profile=True)

    forgot = client.post("/api/auth/forgot-password", json={"email": "faculty@test.edu"})
    assert forgot.status_code == 200

    verify = client.post(
        "/api/auth/forgot-password/verify",
        json={"email": "faculty@test.edu", "code": "654321"},
    )
    assert verify.status_code == 200
    reset_token = verify.get_json()["resetToken"]

    reset = client.post(
        "/api/auth/forgot-password/reset",
        json={
            "email": "faculty@test.edu",
            "resetToken": reset_token,
            "newPassword": "ResetPass99",
        },
    )
    assert reset.status_code == 200
    assert _login(client, "faculty@test.edu", "ResetPass99").status_code == 200


def test_logout_revokes_access_token(client):
    _create_user(email="admin@test.edu", role="administrator", password="AdminPass1")
    login_data = _login(client, "admin@test.edu", "AdminPass1").get_json()
    token = login_data["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/auth/session", headers=headers).status_code == 200
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/auth/session", headers=headers).status_code == 401


def test_refresh_token(client):
    _create_user(email="admin@test.edu", role="administrator", password="AdminPass1")
    login_data = _login(client, "admin@test.edu", "AdminPass1").get_json()
    refresh = client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {login_data['refreshToken']}"},
    )
    assert refresh.status_code == 200
    assert refresh.get_json()["accessToken"]
