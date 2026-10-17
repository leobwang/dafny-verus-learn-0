#!/usr/bin/python3
"""The sandbox image's entry process (/opt/dvl/bin/entry; DV4-PLAN §5.6.2, §5.8).

    entry verify | agent

It starts the relays (Route B, Δ146): for every relay socket that
scripts/mksandbox-run bound under /run/dvl/, a listener on 127.0.0.1 that
forwards each connection to the socket, where the host-side gate (or the
egress proxy) answers. Then it waits, so that the host can stream the
editable files in, run the containment controls and the run's commands with
`docker exec`, and stream /work back out; the host's `docker rm --force`
ends it. It never starts an agent itself, and it reads nothing from /work.

Standard library only; runs as uid 1000 with no capability.
"""

import os
import signal
import socket
import sys
import threading

RELAY_DIR = "/run/dvl"
# socket name -> the loopback port the relay listens on inside the container
RELAYS = {"ollama.sock": 11434, "egress.sock": 3128}
BUF = 65536


def pump(src, dst):
    try:
        while True:
            data = src.recv(BUF)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        for s in (dst,):
            try:
                s.shutdown(socket.SHUT_WR)
            except OSError:
                pass


def serve(conn, path):
    try:
        up = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        up.connect(path)
    except OSError:
        conn.close()
        return
    a = threading.Thread(target=pump, args=(conn, up), daemon=True)
    b = threading.Thread(target=pump, args=(up, conn), daemon=True)
    a.start()
    b.start()
    a.join()
    b.join()
    conn.close()
    up.close()


def relay(port, path):
    ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ls.bind(("127.0.0.1", port))
    ls.listen(16)
    while True:
        conn, _ = ls.accept()
        threading.Thread(target=serve, args=(conn, path), daemon=True).start()


def main(argv):
    if len(argv) != 2 or argv[1] not in ("verify", "agent"):
        print("usage: entry verify|agent", file=sys.stderr)
        return 2
    started = []
    for name, port in sorted(RELAYS.items()):
        path = os.path.join(RELAY_DIR, name)
        if os.path.exists(path):
            threading.Thread(target=relay, args=(port, path), daemon=True).start()
            started.append(f"127.0.0.1:{port} -> {path}")
    print("entry: " + argv[1] + (", relays " + "; ".join(started) if started else ", no relay"),
          file=sys.stderr, flush=True)
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, lambda *_: stop.set())
    while not stop.wait(1.0):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
