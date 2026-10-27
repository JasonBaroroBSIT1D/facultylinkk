from auth.provisioning_service import generate_temporary_password


def test_generate_temporary_password_meets_rules():
    for _ in range(20):
        password = generate_temporary_password()
        assert len(password) >= 14
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)
