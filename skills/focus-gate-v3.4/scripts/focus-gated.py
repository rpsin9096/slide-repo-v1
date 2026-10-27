#!/usr/bin/env python3
"""FocusGate v3.0 — Persistent Autonomous Swarm Supervisor Daemon Entrypoint.

Starts the background Unix domain socket daemon (/tmp/focusgate-v3.sock)
and handles graceful shutdown on SIGINT / SIGTERM.

Zero external dependencies (100% Python standard library).
"""

import os
import sys
import signal
import time

from core.swarm_daemon import SwarmDaemon, DEFAULT_SOCKET_PATH


def main():
    socket_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else DEFAULT_SOCKET_PATH
    workspace_root = os.getcwd()

    daemon = SwarmDaemon(socket_path=socket_path, workspace_root=workspace_root)

    def handle_signal(sig, frame):
        sys.stderr.write(f"\n[focus-gated] Caught signal {sig}, terminating gracefully...\n")
        daemon.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    sys.stdout.write(f"[focus-gated] Starting Swarm Daemon on {socket_path}...\n")
    sys.stdout.flush()
    daemon.run()


if __name__ == '__main__':
    main()
