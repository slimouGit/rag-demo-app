import pytest

from documentservice import normalize_and_validate_url


def test_private_url_is_blocked_localhost():
    """Localhost targets should be blocked by URL validation."""
    with pytest.raises(ValueError):
        normalize_and_validate_url("http://localhost:8000/secret")


def test_private_url_is_blocked_private_ip():
    """Private network IP targets should be blocked by URL validation."""
    with pytest.raises(ValueError):
        normalize_and_validate_url("http://192.168.1.10/internal")
