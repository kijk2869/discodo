import nacl.secret


def xsalsa20_poly1305(key, header, data):
    Box = nacl.secret.SecretBox(bytes(key))
    Nonce = bytearray(24)
    Nonce[:12] = header

    return header + Box.encrypt(bytes(data), bytes(Nonce)).ciphertext


def xsalsa20_poly1305_suffix(key, header, data):
    Box = nacl.secret.SecretBox(bytes(key))
    Nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)

    return header + Box.encrypt(bytes(data), Nonce).ciphertext + Nonce


def getEncryptModes():
    return globals()
