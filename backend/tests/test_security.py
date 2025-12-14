import pytest

from app.utils.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hashing():
    password = "mysecretpassword"

    hashed = hash_password(password)

    assert hashed != password
    assert len(hashed) > 0


def test_password_verification():
    password = "mysecretpassword"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    data = {"sub": "1", "username": "testuser"}

    token = create_access_token(data)

    assert len(token) > 0
    assert token.count(".") == 2


def test_decode_access_token():
    data = {"sub": "1", "username": "testuser"}
    token = create_access_token(data)

    decoded = decode_access_token(token)

    assert decoded.user_id == 1
    assert decoded.username == "testuser"


def test_decode_invalid_token():
    from app.utils.exceptions import AuthenticationError

    with pytest.raises(AuthenticationError):
        decode_access_token("invalid.token.here")
