"""
Encryption utilities for sensitive data storage
Uses Fernet symmetric encryption with a derived key
"""
import os
import base64
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Encryption key file path (stored alongside the database)
KEY_FILE = "data/.encryption_key"


def _get_or_create_key() -> bytes:
    """
    Get or create a persistent encryption key.
    The key is stored in a file to persist across restarts.
    """
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    key_path = KEY_FILE

    if os.path.exists(key_path):
        # Read existing key
        with open(key_path, "rb") as f:
            key = f.read()
        logger.debug("Loaded existing encryption key")
    else:
        # Generate new key
        key = Fernet.generate_key()
        with open(key_path, "wb") as f:
            f.write(key)
        logger.info("Generated new encryption key")

    return key


def _get_fernet() -> Fernet:
    """Get a Fernet instance with the encryption key"""
    key = _get_or_create_key()
    return Fernet(key)


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a string value.
    Returns base64-encoded encrypted data.
    """
    if not plaintext:
        return ""

    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(plaintext.encode('utf-8'))
        # Return as base64 string for storage
        return encrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise ValueError("Failed to encrypt value")


def decrypt_value(encrypted: str) -> str:
    """
    Decrypt an encrypted string value.
    Returns the original plaintext.
    """
    if not encrypted:
        return ""

    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted.encode('utf-8'))
        return decrypted.decode('utf-8')
    except InvalidToken:
        logger.error("Decryption failed: Invalid token (key may have changed)")
        raise ValueError("Failed to decrypt value - encryption key may have changed")
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError("Failed to decrypt value")


def is_encrypted(value: str) -> bool:
    """
    Check if a value appears to be encrypted (Fernet format).
    Fernet tokens start with 'gAAAAA' when base64 encoded.
    """
    if not value:
        return False
    return value.startswith('gAAAAA')


def encrypt_if_not_encrypted(value: str) -> str:
    """
    Encrypt a value only if it's not already encrypted.
    Useful for migrations.
    """
    if not value:
        return ""

    if is_encrypted(value):
        return value

    return encrypt_value(value)


def decrypt_safe(value: str) -> Optional[str]:
    """
    Safely decrypt a value, returning None if decryption fails.
    Useful when the value might be plaintext or encrypted.
    """
    if not value:
        return None

    # If it doesn't look encrypted, return as-is (for backwards compatibility)
    if not is_encrypted(value):
        logger.warning("Value does not appear to be encrypted, returning as-is")
        return value

    try:
        return decrypt_value(value)
    except ValueError:
        logger.error("Failed to decrypt value")
        return None
