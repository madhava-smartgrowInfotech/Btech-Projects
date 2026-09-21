from auth.authentication import signup, login
from utils.security import hash_password, verify_password


def test_password_hashing_roundtrip():
    hashed = hash_password("SuperSecret1!")
    assert hashed != "SuperSecret1!"
    assert verify_password("SuperSecret1!", hashed)
    assert not verify_password("WrongPassword1!", hashed)


def test_signup_success():
    result = signup("Jane Doe", "jane@example.com", "janedoe", "Str0ng!Pass", "Str0ng!Pass")
    assert result.success
    assert result.user_id is not None


def test_signup_rejects_weak_password():
    result = signup("Jane Doe", "jane2@example.com", "janedoe2", "weak", "weak")
    assert not result.success


def test_signup_rejects_mismatched_passwords():
    result = signup("Jane Doe", "jane3@example.com", "janedoe3", "Str0ng!Pass", "Different1!")
    assert not result.success


def test_signup_rejects_duplicate_email():
    signup("Jane Doe", "dupe@example.com", "userone", "Str0ng!Pass", "Str0ng!Pass")
    result = signup("John Doe", "dupe@example.com", "usertwo", "Str0ng!Pass", "Str0ng!Pass")
    assert not result.success
    assert "email" in result.message.lower()


def test_login_success_with_username():
    signup("Jane Doe", "login1@example.com", "loginuser1", "Str0ng!Pass", "Str0ng!Pass")
    result = login("loginuser1", "Str0ng!Pass")
    assert result.success
    assert result.user_id is not None


def test_login_success_with_email():
    signup("Jane Doe", "login2@example.com", "loginuser2", "Str0ng!Pass", "Str0ng!Pass")
    result = login("login2@example.com", "Str0ng!Pass")
    assert result.success


def test_login_fails_with_wrong_password():
    signup("Jane Doe", "login3@example.com", "loginuser3", "Str0ng!Pass", "Str0ng!Pass")
    result = login("loginuser3", "WrongPassword1!")
    assert not result.success


def test_login_fails_for_unknown_user():
    result = login("ghost_user", "Whatever1!")
    assert not result.success
