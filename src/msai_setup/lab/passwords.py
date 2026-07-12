"""SHA-512 crypt (`$6$…`) password hashing, shared across install mechanisms.

Both Ubuntu autoinstall (`identity.password`) and Fedora kickstart
(`user --iscrypted --password=`) want a crypt(3)-format SHA-512 hash rather
than a plaintext password. This module is the single home for that algorithm so
neither cloudinit.py (Ubuntu) nor kickstart.py (Fedora) duplicates it.

Pure-Python on top of `hashlib`: it never shells out to `openssl` (Apple's
bundled LibreSSL `openssl passwd` lacks `-6`) and doesn't need the stdlib
`crypt` module (removed in Python 3.13).
"""

from __future__ import annotations

import hashlib
import secrets

# Alphabet used by crypt(3) for its custom base64 encoding (note: not the
# standard base64 alphabet — `.` and `/` lead, and there is no padding).
_CRYPT_B64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# Byte-permutation order the SHA-512 crypt scheme applies to the final digest
# before base64-encoding it, per the reference implementation (Ulrich Drepper's
# sha512-crypt spec / glibc). Each triple is encoded into 4 output characters.
_SHA512_CRYPT_ORDER = (
    (0, 21, 42), (22, 43, 1), (44, 2, 23), (3, 24, 45),
    (25, 46, 4), (47, 5, 26), (6, 27, 48), (28, 49, 7),
    (50, 8, 29), (9, 30, 51), (31, 52, 10), (53, 11, 32),
    (12, 33, 54), (34, 55, 13), (56, 14, 35), (15, 36, 57),
    (37, 58, 16), (59, 17, 38), (18, 39, 60), (40, 61, 19),
    (62, 20, 41),
)


def _b64_from_24bit(b2: int, b1: int, b0: int, n: int) -> str:
    """Encode up to three bytes into `n` crypt-base64 characters (low bits first)."""
    w = (b2 << 16) | (b1 << 8) | b0
    out: list[str] = []
    for _ in range(n):
        out.append(_CRYPT_B64[w & 0x3F])
        w >>= 6
    return "".join(out)


def sha512_crypt(password: str, *, salt: str | None = None, rounds: int = 5000) -> str:
    """Return a SHA-512 crypt (`$6$…`) hash of `password`.

    A pure-Python implementation of the SHA-512 crypt scheme (built on
    `hashlib`), producing output byte-for-byte compatible with
    crypt(3) / `openssl passwd -6`.

    Args:
        password: The plaintext password to hash.
        salt: Up to 16 chars from the crypt base64 alphabet. Random if omitted.
        rounds: SHA-512 crypt round count (5000 is the crypt(3) default).

    Returns:
        A `$6$<salt>$<hash>` string compatible with crypt(3)/`openssl passwd -6`.
    """
    if salt is None:
        salt = "".join(secrets.choice(_CRYPT_B64) for _ in range(16))
    pw = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")[:16]
    pw_len = len(pw)

    # Digest "A": password + salt + digest "B"-derived bytes.
    ctx = hashlib.sha512()
    ctx.update(pw)
    ctx.update(salt_bytes)

    alt = hashlib.sha512()
    alt.update(pw)
    alt.update(salt_bytes)
    alt.update(pw)
    alt_result = alt.digest()

    cnt = pw_len
    while cnt > 64:
        ctx.update(alt_result)
        cnt -= 64
    ctx.update(alt_result[:cnt])

    cnt = pw_len
    while cnt > 0:
        ctx.update(alt_result if cnt & 1 else pw)
        cnt >>= 1

    digest_a = ctx.digest()

    # Sequence "P": password repeated, sized to the password length.
    dp_ctx = hashlib.sha512()
    for _ in range(pw_len):
        dp_ctx.update(pw)
    dp = dp_ctx.digest()
    p_bytes = b""
    cnt = pw_len
    while cnt > 64:
        p_bytes += dp
        cnt -= 64
    p_bytes += dp[:cnt]

    # Sequence "S": salt repeated (16 + first digest byte) times, sized to salt.
    ds_ctx = hashlib.sha512()
    for _ in range(16 + digest_a[0]):
        ds_ctx.update(salt_bytes)
    ds = ds_ctx.digest()
    s_bytes = b""
    cnt = len(salt_bytes)
    while cnt > 64:
        s_bytes += ds
        cnt -= 64
    s_bytes += ds[:cnt]

    # The stretching loop that makes the hash expensive to brute-force.
    c = digest_a
    for i in range(rounds):
        loop = hashlib.sha512()
        loop.update(p_bytes if i & 1 else c)
        if i % 3:
            loop.update(s_bytes)
        if i % 7:
            loop.update(p_bytes)
        loop.update(c if i & 1 else p_bytes)
        c = loop.digest()

    encoded = "".join(_b64_from_24bit(c[b2], c[b1], c[b0], 4) for b2, b1, b0 in _SHA512_CRYPT_ORDER)
    encoded += _b64_from_24bit(0, 0, c[63], 2)
    return f"$6${salt}${encoded}"
