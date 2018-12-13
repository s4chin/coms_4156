import base64
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHA256
import crypto as Crypto
PADDING = "="


def test_key_to_store():
    crypto = Crypto.Crypto()
    input_string = ["hello", ""]
    flag = 1
    for i in input_string:
        if crypto.key_to_store(i) == SHA256.new(i.encode()).hexdigest():
            flag = flag & 1
        else:
            flag = 0

    assert flag == 1


def test_key_hash():
    crypto = Crypto.Crypto()
    input_string = ["hello", ""]
    flag = 1
    for i in input_string:
        if crypto.key_hash(i) == SHA256.new(i.encode()).digest():
            flag = flag & 1
        else:
            flag = 0

    assert flag == 1


def test_encrypt():
    crypto = Crypto.Crypto()
    input_string = [("hello", "key"), ("hello2", ""), ("", "key"), ("", "")]
    flag = 1
    for i in input_string:
        text, key = i[0], i[1]
        answer = crypto.encrypt(text, key)
        while len(text) % 16 != 0:
            text += PADDING
        cipher = AES.new(crypto.key_hash(key), AES.MODE_ECB)
        encrypted = cipher.encrypt(text.encode())
        if answer == base64.b64encode(encrypted).decode():
            flag = flag & 1
        else:
            flag = 0

    assert flag == 1


def test_decrypt():
    crypto = Crypto.Crypto()
    input_string = [("hello", "key"), ("hello2", ""), ("", "key"), ("", "")]
    flag = 1
    for i in input_string:
        text, key = i[0], i[1]
        while len(text) % 16 != 0:
            text += PADDING
        cipher = AES.new(crypto.key_hash(key), AES.MODE_ECB)
        encrypted = cipher.encrypt(text.encode())
        encrypted = base64.b64encode(encrypted).decode()
        cipher = AES.new(crypto.key_hash(key), AES.MODE_ECB)
        plain = cipher.decrypt(base64.b64decode(encrypted))
        if i[0] == plain.decode().rstrip(PADDING):
            flag = flag & 1
        else:
            flag = 0
    assert flag == 1
