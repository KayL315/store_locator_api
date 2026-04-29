from auth import hash_password, verify_password


def test_hash_password():
    password = "TestPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert isinstance(hashed, str)


def test_verify_password_success():
    password = "TestPassword123!"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_fail():
    password = "TestPassword123!"
    wrong_password = "WrongPassword123!"
    hashed = hash_password(password)

    assert verify_password(wrong_password, hashed) is False