#!/usr/bin/env python3
"""
基于 cryptography 库的 Ed25519 签名实现
"""

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)


class SigningKey:

    def __init__(self, private_key: Ed25519PrivateKey):
        self._key = private_key

    @classmethod
    def from_seed(cls, seed: bytes) -> "SigningKey":
        """从 32 字节种子生成签名密钥"""
        if len(seed) != 32:
            raise ValueError(f"seed 必须是 32 字节，当前为 {len(seed)} 字节")
        return cls(Ed25519PrivateKey.from_private_bytes(seed))

    @classmethod
    def generate(cls) -> "SigningKey":
        """随机生成签名密钥"""
        return cls(Ed25519PrivateKey.generate())

    def get_public_key(self) -> bytes:
        """返回 32 字节原始公钥"""
        return self._key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    def get_verify_key(self) -> "VerifyKey":
        return VerifyKey(self.get_public_key())

    def sign(self, message: bytes) -> bytes:
        """返回 64 字节签名"""
        return self._key.sign(message)

    def to_bytes(self) -> bytes:
        """导出原始私钥字节（即 seed）"""
        return self._key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())


class VerifyKey:

    def __init__(self, public_key: bytes):
        if len(public_key) != 32:
            raise ValueError("公钥必须是 32 字节")
        self._key: Ed25519PublicKey = Ed25519PublicKey.from_public_bytes(public_key)
        self._public_key = public_key

    def verify(self, message: bytes, signature: bytes) -> bool:
        """验证签名，合法返回 True，否则返回 False"""
        try:
            self._key.verify(signature, message)
            return True
        except InvalidSignature:
            return False

    def to_bytes(self) -> bytes:
        return self._public_key
