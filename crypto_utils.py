import os
from cryptography.fernet import Fernet, InvalidToken

_KEY = os.environ.get("ENCRYPTION_KEY")
if not _KEY:
    raise RuntimeError(
        "ENCRYPTION_KEY .env dosyasinda tanimli degil. "
        "Uretmek icin: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

_fernet = Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)

def encrypt(value):
    if value is None or value == "":
        return value
    if isinstance(value, bytes):
        value = value.decode()
    return _fernet.encrypt(value.encode()).decode()

def decrypt(value):
    if value is None or value == "":
        return value
    if isinstance(value, bytes):
        value = value.decode()
    try:
        return _fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        return value
