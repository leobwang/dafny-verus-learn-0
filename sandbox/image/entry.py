#!/usr/bin/python3
"""The sandbox image's entry process (/opt/dvl/bin/entry; DV4-PLAN §5.6.2, §5.8;
DELTAS Δ504).

    entry verify | agent      a sandbox container
    entry gate HOST PORT      a run's gate container

A sandbox container (`verify`, `agent`) starts the relays of its run: for
every entry of /run/dvl/relays.json ({"<loopback port>": ["<host>", <port>]},
which scripts/mksandbox-run binds read-only for a model network run), a
listener on 127.0.0.1:<loopback port> that forwards each connection over TCP
to <host>:<port>, the run's gate container on the run's internal network
(Route C: an --internal network with no host address on its bridge, so the
gate container is the one peer the sandbox can reach). Then it waits, so that
the host can stream the editable files in, run the containment controls and
the run's commands with `docker exec`, and stream /work back out; the host's
`docker rm --force` ends it. It never starts an agent itself, and it reads
nothing from /work.

The gate container (`gate HOST PORT`) listens on 0.0.0.0:8000 on the run's
internal network and forwards each connection to HOST:PORT, the host-side
model gate (sandbox/hostside/model_gate.py: on Linux the gateway address of
the run's upstream bridge, on macOS host.docker.internal). It forwards to
that one address only and holds no state; the host gate is the policy.

Standard library only; runs as uid 1000 with no capability.
"""

import json
import signal
import socket
import sys
import threading

RELAYS_FILE = "/run/dvl/relays.json"
GATE_PORT = 8000      # the model API port (Δ505)
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
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def serve(conn, host, port):
    try:
        up = socket.create_connection((host, port), timeout=30)
        up.settimeout(None)
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


def listen(addr, port, host, tport):
    ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ls.bind((addr, port))
    ls.listen(16)
    while True:
        conn, _ = ls.accept()
        threading.Thread(target=serve, args=(conn, host, tport), daemon=True).start()


def relays():
    """[(loopback port, host, port)] of /run/dvl/relays.json (absent: none)."""
    try:
        with open(RELAYS_FILE, encoding="utf-8") as fh:
            spec = json.load(fh)
    except FileNotFoundError:
        return []
    return [(int(lport), str(host), int(port)) for lport, (host, port) in sorted(spec.items())]


def wait_forever():
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, lambda *_: stop.set())
    while not stop.wait(1.0):
        pass


def main(argv):
    if len(argv) == 4 and argv[1] == "gate":
        host, port = argv[2], int(argv[3])
        threading.Thread(target=listen, args=("0.0.0.0", GATE_PORT, host, port),
                         daemon=True).start()
        print(f"entry: gate, 0.0.0.0:{GATE_PORT} -> {host}:{port}", file=sys.stderr, flush=True)
        wait_forever()
        return 0
    if len(argv) != 2 or argv[1] not in ("verify", "agent"):
        print("usage: entry verify|agent | entry gate HOST PORT", file=sys.stderr)
        return 2
    started = []
    for lport, host, port in relays():
        threading.Thread(target=listen, args=("127.0.0.1", lport, host, port),
                         daemon=True).start()
        started.append(f"127.0.0.1:{lport} -> {host}:{port}")
    print("entry: " + argv[1] + (", relays " + "; ".join(started) if started else ", no relay"),
          file=sys.stderr, flush=True)
    wait_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
