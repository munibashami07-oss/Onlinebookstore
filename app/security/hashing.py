"""Password hashing and verification utilities using passlib and bcrypt."""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Generate bcrypt hash for a raw password string.

    Args:
        password: Plain text password string.

    Returns:
        Hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored bcrypt hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Stored bcrypt hashed password.

    Returns:
        True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)
