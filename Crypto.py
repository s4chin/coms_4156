import base64
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHA256


class Crypto:
    PADDING = "="

    def key_to_store(self, key):
        return SHA256.new(key.encode()).hexdigest()

    def key_hash(self, key):
        return SHA256.new(key.encode()).digest()

    def encrypt(self, text, key):
        while len(text) % 16 != 0:
            text += self.PADDING
        cipher = AES.new(self.key_hash(key), AES.MODE_ECB)
        encrypted = cipher.encrypt(text.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, text, key):
        cipher = AES.new(self.key_hash(key), AES.MODE_ECB)
        plain = cipher.decrypt(base64.b64decode(text))
        return plain.decode().rstrip(self.PADDING)
