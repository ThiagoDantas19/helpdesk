from cryptography.fernet import Fernet
import base64, hashlib


def _derivar_chave(secret_key):
    if isinstance(secret_key, str):
        secret_key = secret_key.encode()
    return base64.urlsafe_b64encode(hashlib.sha256(secret_key).digest())


def encrypt(plaintext, secret_key):
    if not plaintext:
        return None
    f = Fernet(_derivar_chave(secret_key))
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext, secret_key):
    if not ciphertext:
        return None
    f = Fernet(_derivar_chave(secret_key))
    return f.decrypt(ciphertext.encode()).decode()
