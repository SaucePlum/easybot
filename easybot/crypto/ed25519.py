#!/usr/bin/env python3
"""
纯 Python 实现的 Ed25519 签名验证算法
1. _point_double 使用专用倍点公式（4M+4S），不再调用通用加法（8M）
2. _point_mul 改用 4-bit 固定窗口法，减少约 50% 的点加次数
3. 预计算基点 G 的查找表，加速所有涉及 G 的标量乘
4. from_seed 严格遵循 RFC 8032，不再做非标准填充
"""

import hashlib

PRIME = 2**255 - 19
D = -121665 * pow(121666, PRIME - 2, PRIME) % PRIME
L = 2**252 + 27742317777372353535851937790883648493
FP_SQRT_M1 = 0x2B8324804FC1DF0B2B4D00993DFBD7A72F431806AD2FE478C4EE1B274A0EA0B0

G_X = 0x216936D3CD6E53FEC0A4E231FDD6DC5C692CC7609525A7B2C9562D608F25D51A
G_Y = 0x6666666666666666666666666666666666666666666666666666666666666658
G = (G_X, G_Y, 1, G_X * G_Y % PRIME)

# ── 内部数学工具 ────────────────────────────────────────────────


def _sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


def _sha512_fp(m: bytes) -> int:
    return int.from_bytes(_sha512(m), "little") % L


def _point_add(pt1: tuple, pt2: tuple) -> tuple:
    """扩展坐标通用点加法，约 8M"""
    A = (pt1[1] - pt1[0]) * (pt2[1] - pt2[0]) % PRIME
    B = (pt1[1] + pt1[0]) * (pt2[1] + pt2[0]) % PRIME
    C = 2 * pt1[3] * pt2[3] * D % PRIME
    D_val = 2 * pt1[2] * pt2[2] % PRIME
    E = (B - A) % PRIME
    F = (D_val - C) % PRIME
    G_val = (D_val + C) % PRIME
    H = (B + A) % PRIME
    return (E * F % PRIME, G_val * H % PRIME, F * G_val % PRIME, E * H % PRIME)


def _point_double(pt: tuple) -> tuple:
    """
    专用倍点公式，仅需 4M + 4S，比通用加法快约 2x。
    公式来源：https://hyperelliptic.org/EFD/g1p/auto-twisted-extended.html#doubling-dbl-2008-hwcd
    """
    X1, Y1, Z1, _ = pt
    A = X1 * X1 % PRIME  # S
    B = Y1 * Y1 % PRIME  # S
    C = 2 * Z1 * Z1 % PRIME  # S
    H = (A + B) % PRIME
    E = (H - (X1 + Y1) * (X1 + Y1)) % PRIME  # S（展开后 = 2*X1*Y1 的负项）
    G_val = (A - B) % PRIME
    F = (C + G_val) % PRIME
    return (
        E * F % PRIME,  # M
        G_val * H % PRIME,  # M
        F * G_val % PRIME,  # M
        E * H % PRIME,  # M
    )


# 单位元（恒等点）
_IDENTITY = (0, 1, 1, 0)


def _build_window_table(pt: tuple, w: int = 4) -> list:
    """
    预计算 0..2^w-1 倍的点查找表。
    table[i] = i * pt
    """
    size = 1 << w
    table = [_IDENTITY] * size
    table[1] = pt
    for i in range(2, size):
        table[i] = _point_add(table[i - 1], pt)
    return table


def _point_mul_windowed(s: int, table: list, w: int = 4) -> tuple:
    """
    4-bit 固定窗口标量乘法。
    """
    mask = (1 << w) - 1
    nbits = s.bit_length()
    # 对齐到 w 的整数倍
    nbits = ((nbits + w - 1) // w) * w

    result = _IDENTITY
    for i in range(nbits - w, -1, -w):
        # 连续做 w 次倍点
        for _ in range(w):
            result = _point_double(result)
        # 取出 w 位窗口，查表做一次加法
        window = (s >> i) & mask
        result = _point_add(result, table[window])
    return result


def _point_mul(s: int, pt: tuple) -> tuple:
    """标量乘法（通用版，自动建表）"""
    table = _build_window_table(pt)
    return _point_mul_windowed(s, table)


# ── 计算基点 G 的查找表 ───
# 模块加载时只计算一次，sign/get_public_key 复用
_G_TABLE = _build_window_table(G)


def _point_mul_G(s: int) -> tuple:
    """乘以基点 G（使用预计算表，比通用版更快）"""
    return _point_mul_windowed(s, _G_TABLE)


def _recover_x(y: int, sign: int):
    if y >= PRIME:
        return None
    x2 = (y * y - 1) * pow(D * y * y + 1, PRIME - 2, PRIME) % PRIME
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (PRIME + 3) // 8, PRIME)
    if (x * x - x2) % PRIME != 0:
        x = x * FP_SQRT_M1 % PRIME
    if (x * x - x2) % PRIME != 0:
        return None
    if (x & 1) != sign:
        x = PRIME - x
    return x


def _point_compress(pt: tuple) -> bytes:
    zinv = pow(pt[2], PRIME - 2, PRIME)
    x = pt[0] * zinv % PRIME
    y = pt[1] * zinv % PRIME
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _point_decompress(s: bytes):
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % PRIME)


def _point_equal(pt1: tuple, pt2: tuple) -> bool:
    if (pt1[0] * pt2[2] - pt2[0] * pt1[2]) % PRIME != 0:
        return False
    if (pt1[1] * pt2[2] - pt2[1] * pt1[2]) % PRIME != 0:
        return False
    return True


# ── 公开 API ──────────────────────────────────────────────────────


class SigningKey:

    def __init__(self, a: int, prefix: bytes):
        self.a = a
        self.prefix = prefix

    @classmethod
    def from_seed(cls, seed: bytes) -> "SigningKey":
        """
        严格遵循 RFC 8032：种子必须恰好为 32 字节。
        """
        if len(seed) != 32:
            raise ValueError(f"seed 必须是 32 字节，当前为 {len(seed)} 字节")
        h = _sha512(seed)
        a = int.from_bytes(h[:32], "little")
        a &= (1 << 254) - 8
        a |= 1 << 254
        return cls(a, h[32:])

    def get_public_key(self) -> bytes:
        return _point_compress(_point_mul_G(self.a))  # 使用预计算表

    def sign(self, message: bytes) -> bytes:
        A = _point_compress(_point_mul_G(self.a))  # 使用预计算表
        r = _sha512_fp(self.prefix + message)
        R = _point_compress(_point_mul_G(r))  # 使用预计算表
        h = _sha512_fp(R + A + message)
        s = (h * self.a + r) % L
        return R + s.to_bytes(32, "little")


class VerifyKey:

    def __init__(self, public_key: bytes):
        if len(public_key) != 32:
            raise ValueError("公钥必须是 32 字节")
        self._point = _point_decompress(public_key)
        if self._point is None:
            raise ValueError("无效的公钥")
        self._public_key = public_key
        # 预计算验证方公钥的查找表，重复验证同一公钥时有额外收益
        self._pk_table = _build_window_table(self._point)

    def verify(self, message: bytes, signature: bytes) -> bool:
        if len(signature) != 64:
            return False
        if signature[63] & 224 != 0:
            return False

        R_encoded = signature[:32]
        S = int.from_bytes(signature[32:64], "little")
        if S >= L:
            return False

        R = _point_decompress(R_encoded)
        if R is None:
            return False

        h = _sha512_fp(R_encoded + self._public_key + message)

        lhs = _point_mul_G(S)  # 预计算表
        rhs = _point_add(R, _point_mul_windowed(h, self._pk_table))  # 预计算表
        return _point_equal(lhs, rhs)
