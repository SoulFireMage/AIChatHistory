from cryptography.fernet import Fernet
from ..config import get_settings


def get_cipher():
    """Get Fernet cipher from settings."""
    settings = get_settings()
    return Fernet(settings.encryption_key.encode())


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key."""
    cipher = get_cipher()
    encrypted = cipher.encrypt(api_key.encode())
    return encrypted.decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key."""
    cipher = get_cipher()
    decrypted = cipher.decrypt(encrypted_key.encode())
    return decrypted.decode()
