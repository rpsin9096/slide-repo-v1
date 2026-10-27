#!/usr/bin/env python3
"""FocusGate v3.1 Loop 54 Test Suite — High-Throughput Wire Binary Protocol."""
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.sdk.wire_protocol import (
    FRAME_PING,
    FRAME_PONG,
    FRAME_EVENT,
    FRAME_DELTA,
    pack_frame,
    unpack_frame,
    StreamingWireFramer,
)


class TestWireProtocol(unittest.TestCase):
    def test_pack_and_unpack_frame(self):
        payload = b'{"action": "merge", "gate_id": "gate-01"}'
        frame = pack_frame(msg_type=FRAME_EVENT, flags=0, payload=payload)
        self.assertTrue(frame.startswith(b"FG\x03\x01"))

        msg_type, flags, unpacked_payload, consumed = unpack_frame(frame)
        self.assertEqual(msg_type, FRAME_EVENT)
        self.assertEqual(flags, 0)
        self.assertEqual(unpacked_payload, payload)
        self.assertEqual(consumed, len(frame))

    def test_corrupted_checksum_raises(self):
        payload = b"state_delta"
        frame = bytearray(pack_frame(msg_type=FRAME_DELTA, flags=0, payload=payload))
        # Corrupt one byte of payload
        frame[11] ^= 0xFF
        with self.assertRaises(ValueError):
            unpack_frame(bytes(frame))

    def test_corrupted_magic_raises(self):
        payload = b"ping"
        frame = bytearray(pack_frame(msg_type=FRAME_PING, flags=0, payload=payload))
        frame[0] = ord("X")
        with self.assertRaises(ValueError):
            unpack_frame(bytes(frame))

    def test_streaming_wire_framer_chunked(self):
        framer = StreamingWireFramer()
        p1 = b"chunk-payload-1"
        p2 = b"chunk-payload-2"
        f1 = pack_frame(FRAME_PING, 0, p1)
        f2 = pack_frame(FRAME_PONG, 0, p2)

        stream = f1 + f2
        # Feed in arbitrary slice sizes (e.g. 7 bytes each)
        frames_received = []
        for i in range(0, len(stream), 7):
            framer.feed(stream[i : i + 7])
            while True:
                item = framer.pop_frame()
                if item is None:
                    break
                frames_received.append(item)

        self.assertEqual(len(frames_received), 2)
        self.assertEqual(frames_received[0], (FRAME_PING, 0, p1))
        self.assertEqual(frames_received[1], (FRAME_PONG, 0, p2))


class TestWireProtocolCLI(unittest.TestCase):
    def test_cli_wire_bench(self):
        import subprocess
        import json
        cmd = [
            sys.executable,
            os.path.join(ROOT, "scripts", "focus-gate.py"),
            "--wire-bench",
            "1000",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("packets", data)
        self.assertIn("throughput_mb_s", data)
        self.assertGreater(data["throughput_mb_s"], 0.0)


if __name__ == "__main__":
    unittest.main()
