#!/usr/bin/env python3
"""
加密算法模块

提供 Ed25519 签名和验证功能。
"""

from .ed25519 import SigningKey, VerifyKey

__all__ = ["SigningKey", "VerifyKey"]
