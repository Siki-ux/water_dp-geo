#!/usr/bin/env python3
import os

import pytest
from timeio.crypto import decrypt, encrypt, get_crypt_key
from cryptography.fernet import Fernet, InvalidToken


@pytest.fixture(scope="module", autouse=True)
def create_secret():
    """Create a new Fernet for testing.

    We always create a NEW fernet key and use it for the tests,
    because if a (production-) key is already present in the
    environment, it might get exposed in test logs.
    """
    os.environ["FERNET_ENCRYPTION_SECRET"] = Fernet.generate_key().decode()


def test_get_crypt_key():
    assert get_crypt_key() == os.environ["FERNET_ENCRYPTION_SECRET"]


@pytest.fixture(
    scope="function",
    params=["spam", "ham", "And Now for Something Completely Different"],
)
def data(request):
    return request.param


def test_encrypt(data):
    # We cant use static data here, because each call to encrypt will
    # return a different ciphertext, BUT we can check for that ;)
    key = get_crypt_key()
    ciphertext1 = encrypt(data, key)
    ciphertext2 = encrypt(data, key)
    assert ciphertext1 != ciphertext2


@pytest.mark.parametrize(
    "key, plaintext, ciphertext",
    [
        (
            "mbOzgT5FxKu6pCToXuG46PdAvbvki5AOBcKUfjfjmao=",
            "some text",
            "gAAAAABnm4d8nLhGCBYOK7KiI5CkXHRQOTv2byw8Fws4QCdJFJPKnCC7chFp632UYgJ43nB0MaBNK5_kT8acUw-ki-EcwY9XGQ==",
        ),
        (
            "Rpxuw3kfjHgOpEhJR-35gO_sg6LN5gTHVNILDz5NK28=",
            "And Now for Something Completely Different",
            "gAAAAABnm4hgBcI5Lnv_i90PYwV9hPpL2QHDkiXlXW1UlIZgCQKvWpXtoZa9ekGd3YXbG3GlD6UnYTA0dZNLy5zhvCqzw_Mj2qrNh2DvIxzqbYH-YaIItZ-pP9_WQQ8PtklTh-O0DKCK",
        ),
    ],
)
def test_decrypt(key, plaintext, ciphertext):
    assert decrypt(ciphertext, key) == plaintext
    bad_key = Fernet.generate_key().decode()
    with pytest.raises(InvalidToken):
        decrypt(ciphertext, bad_key)


def test_roundtrip_crypt(data):
    key = get_crypt_key()
    assert decrypt(encrypt(data, key), key) == data
