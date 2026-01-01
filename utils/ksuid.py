"""
KSUID - K-Sortable Unique Identifier.

Time-sortable, globally unique IDs without coordination.
Format: 4 bytes timestamp + 16 bytes random = 27 char base62 string.
"""

import os
import struct
import time

# KSUID epoch: 2014-05-13
KSUID_EPOCH = 1400000000
BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def generate_ksuid():
    """Generate a 27-character sortable unique ID."""
    # 4 bytes: seconds since KSUID epoch
    timestamp = int(time.time()) - KSUID_EPOCH
    ts_bytes = struct.pack(">I", timestamp)
    
    # 16 bytes: random
    random_bytes = os.urandom(16)
    
    # Combine and encode as base62
    raw = ts_bytes + random_bytes
    n = int.from_bytes(raw, byteorder="big")
    
    chars = []
    while n > 0:
        n, remainder = divmod(n, 62)
        chars.append(BASE62[remainder])
    
    return "".join(reversed(chars)).rjust(27, "0")
