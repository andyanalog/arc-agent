from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets
import logging

logger = logging.getLogger(__name__)

# Initialize Argon2 hasher with secure parameters
ph = PasswordHasher(
    time_cost=2,  # Number of iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,  # Number of parallel threads
    hash_len=32,  # Length of hash in bytes
    salt_len=16  # Length of salt in bytes
)


def hash_pin(pin: str) -> str:
    """
    Hash a PIN using Argon2id
    
    Args:
        pin: The PIN to hash (should be validated before calling)
    
    Returns:
        Hashed PIN string
    """
    try:
        # Argon2 automatically generates a random salt and includes it in the hash
        hashed = ph.hash(pin)
        logger.info("PIN hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Failed to hash PIN: {str(e)}")
        raise


def verify_pin(stored_hash: str, provided_pin: str) -> bool:
    """
    Verify a PIN against its stored hash
    
    Args:
        stored_hash: The stored Argon2 hash
        provided_pin: The PIN to verify
    
    Returns:
        True if PIN matches, False otherwise
    """
    try:
        ph.verify(stored_hash, provided_pin)
        
        # Check if hash needs rehashing (algorithm updated)
        if ph.check_needs_rehash(stored_hash):
            logger.info("Hash needs rehashing with updated parameters")
        
        return True
    except VerifyMismatchError:
        logger.warning("PIN verification failed")
        return False
    except Exception as e:
        logger.error(f"PIN verification error: {str(e)}")
        return False


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token
    
    Args:
        length: Number of bytes (will be encoded to longer string)
    
    Returns:
        URL-safe random token
    """
    return secrets.token_urlsafe(length)


def validate_pin_format(pin: str) -> tuple[bool, str]:
    """
    Validate PIN format and strength
    
    Args:
        pin: The PIN to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not pin or len(pin) != 6:
        return False, "PIN must be exactly 6 digits"
    
    if not pin.isdigit():
        return False, "PIN must contain only digits"
    
    # Check for weak patterns
    weak_patterns = [
        ('123456', '123456 or sequential patterns'),
        ('654321', '654321 or sequential patterns'),
        ('000000', 'all same digits'),
        ('111111', 'all same digits'),
        ('222222', 'all same digits'),
        ('333333', 'all same digits'),
        ('444444', 'all same digits'),
        ('555555', 'all same digits'),
        ('666666', 'all same digits'),
        ('777777', 'all same digits'),
        ('888888', 'all same digits'),
        ('999999', 'all same digits'),
    ]
    
    for pattern, description in weak_patterns:
        if pin == pattern:
            return False, f"PIN is too weak: cannot use {description}"
    
    # Check for too few unique digits
    unique_digits = len(set(pin))
    if unique_digits <= 2:
        return False, "PIN is too weak: use more different digits"
    
    return True, ""