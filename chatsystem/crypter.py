import params
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256


BS = params.AES_BLOCKSIZE
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s : s[:-ord(s[len(s)-1:])]


class AES_Crypter:
    def __init__(self, key, iv):
        self.key = key
        self.iv = iv
        self.cipher = AES.new(self.key, AES.MODE_CBC, self.iv)

    def encrypt(self, message):
        return self.cipher.encrypt(pad(message))

    def decrypt(self, ciphertext):
        return unpad(self.cipher.decrypt(ciphertext))


the_rsa_crypter = None
def get_rsa_crypter():
    global the_rsa_crypter
    if the_rsa_crypter is None:
        the_rsa_crypter = RSA_Crypter()
    return the_rsa_crypter


class RSA_Crypter:
    def __init__(self):
        self.rsa_key = RSA.generate(params.RSA_KEYLENGTH)
        self.rsa_key_public = self.rsa_key.publickey()
        self.cipher = PKCS1_OAEP.new(self.rsa_key, SHA256.new())

    def get_rsa_key_obj(self):
        return self.rsa_key

    def get_rsa_key_obj_public(self):
        return self.rsa_key_public

    def rsa_public_key_to_string(self):
        bytes = self.rsa_key_public.exportKey('PEM')
        key_string = bytes.decode('utf-8')
        return key_string

    def rsa_public_key_to_string_extern(self, key):
        bytes = key.exportKey('PEM')
        key_string = bytes.decode('utf-8')
        return key_string

    def rsa_key_to_string(self):
        bytes = self.rsa_key.exportKey('PEM')
        key_string = bytes.decode('utf-8')
        return key_string

    def encrypt(self, message):
        if self.cipher.can_encrypt():
            bytes = self.cipher.encrypt(message)
            return bytes
        else:
            print("Cipher cannot encrypt")
            return None

    def encrypt_client_pubkey(self, public_key, message):
        cipher = PKCS1_OAEP.new(public_key, SHA256.new())
        if cipher.can_encrypt():
            bytes = cipher.encrypt(message.encode())
            return bytes
        else:
            print('Cipher cannot encrypt')
            return None

    def decrypt(self, ciphertext):
        return self.cipher.decrypt(ciphertext)
