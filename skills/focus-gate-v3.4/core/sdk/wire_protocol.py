"""FocusGate v3.1 Loop 54 — High-Throughput Wire Binary Protocol.

Compact, zero-copy binary framing protocol for grid socket nodes and IPC.
Frames are delineated by a 4-byte magic signature, 1-byte message type,
1-byte flags, 4-byte payload length, raw payload, and a 4-byte CRC32 trailer.

Zero external dependencies (100% Python stdlib).
"""

import zlib
import struct
from typing import Tuple, Optional, List

MAGIC_HEADER = b"FG\x03\x01"

FRAME_PING = 1
FRAME_PONG = 2
FRAME_EVENT = 3
FRAME_HEARTBEAT = 4
FRAME_DELTA = 5

FLAG_NONE = 0x00
FLAG_COMPRESSED = 0x01
FLAG_ENCRYPTED = 0x02
FLAG_URGENT = 0x04

HEADER_FORMAT = ">4sBBI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
TRAILER_FORMAT = ">I"
TRAILER_SIZE = struct.calcsize(TRAILER_FORMAT)
MIN_FRAME_SIZE = HEADER_SIZE + TRAILER_SIZE


def pack_frame(msg_type: int, flags: int, payload: bytes) -> bytes:
    """Serializes a message into a binary frame with header and CRC32 trailer."""
    payload_len = len(payload)
    header = struct.pack(HEADER_FORMAT, MAGIC_HEADER, msg_type, flags, payload_len)
    # Checksum covers type + flags + payload_len + payload
    crc = zlib.crc32(header[4:] + payload) & 0xFFFFFFFF
    trailer = struct.pack(TRAILER_FORMAT, crc)
    return header + payload + trailer


def unpack_frame(data: bytes) -> Tuple[int, int, bytes, int]:
    """Deserializes a single binary frame from bytes.

    Returns:
        (msg_type, flags, payload, consumed_bytes)

    Raises:
        ValueError: If magic header is invalid, checksum fails, or data is truncated.
    """
    if len(data) < MIN_FRAME_SIZE:
        raise ValueError("Incomplete frame data (under minimum frame size)")

    magic, msg_type, flags, payload_len = struct.unpack_from(HEADER_FORMAT, data, 0)
    if magic != MAGIC_HEADER:
        raise ValueError(f"Invalid frame magic header: {magic!r}")

    total_len = HEADER_SIZE + payload_len + TRAILER_SIZE
    if len(data) < total_len:
        raise ValueError("Incomplete payload in frame")

    payload = data[HEADER_SIZE : HEADER_SIZE + payload_len]
    (expected_crc,) = struct.unpack_from(TRAILER_FORMAT, data, HEADER_SIZE + payload_len)

    computed_crc = zlib.crc32(data[4 : HEADER_SIZE + payload_len]) & 0xFFFFFFFF
    if computed_crc != expected_crc:
        raise ValueError(f"CRC32 mismatch: expected {expected_crc:#010x}, computed {computed_crc:#010x}")

    return msg_type, flags, payload, total_len


class StreamingWireFramer:
    """Stateful stream buffer decoder that yields complete, validated frames."""

    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, chunk: bytes) -> None:
        """Appends raw chunk from socket or stream to the internal buffer."""
        self._buf.extend(chunk)

    def pop_frame(self) -> Optional[Tuple[int, int, bytes]]:
        """Extracts the next complete frame from buffer, or returns None if incomplete."""
        # Use bounded loop to strictly avoid any infinite loop hazards
        max_attempts = len(self._buf) + 1
        attempts = 0

        while len(self._buf) >= MIN_FRAME_SIZE and attempts < max_attempts:
            attempts += 1
            # Resynchronize if stream doesn't start with magic header
            if self._buf[:4] != MAGIC_HEADER:
                magic_idx = self._buf.find(MAGIC_HEADER)
                if magic_idx == -1:
                    # Keep last 3 bytes in case magic is split across chunks
                    keep_len = min(3, len(self._buf))
                    del self._buf[:-keep_len]
                    return None
                else:
                    del self._buf[:magic_idx]

            if len(self._buf) < MIN_FRAME_SIZE:
                return None

            try:
                msg_type, flags, payload, consumed = unpack_frame(bytes(self._buf))
                del self._buf[:consumed]
                return msg_type, flags, payload
            except ValueError as e:
                # If error is due to incomplete payload, await more bytes
                if "Incomplete" in str(e):
                    return None
                # If corruption, drop one byte to seek next frame
                del self._buf[0]

        return None
