"""The harness tests' network tripwire (harness/tests/conftest.py; DV4-PLAN §9).

Every refusal here is a plain operation that must fail: no address is ever
reached, because the tripwire raises before the real connect runs."""

import http.server
import pathlib
import socket
import threading
import urllib.request

import pytest

pytest_plugins = ["pytester"]


def test_an_unregistered_address_is_refused_before_connecting(net_trips):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with pytest.raises(RuntimeError, match="network tripwire"):
        s.connect(("127.0.0.1", 8000))          # the course's model server (Δ505)
    s.close()
    assert len(net_trips) == 1 and "8000" in net_trips[0]
    net_trips.clear()


def test_name_lookups_ipv6_udp_and_unix_sockets_are_refused(net_trips):
    with pytest.raises(RuntimeError):
        socket.getaddrinfo("api.anthropic.com", 443)
    with pytest.raises(RuntimeError):
        socket.create_connection(("::1", 22), timeout=1)
    u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with pytest.raises(RuntimeError):
        u.sendto(b"x", ("127.0.0.53", 53))
    u.close()
    x = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    with pytest.raises(RuntimeError):
        x.connect("/var/run/docker.sock")
    x.close()
    assert len(net_trips) == 4
    net_trips.clear()


def test_a_registered_fake_server_is_reachable(net_allow):
    class Hello(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"fake")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Hello)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        net_allow(server.server_address)
        host, port = server.server_address
        with urllib.request.urlopen(f"http://{host}:{port}/", timeout=5) as r:
            assert r.read() == b"fake"
    finally:
        server.shutdown()
        server.server_close()


def test_a_swallowed_refusal_still_fails_the_test(pytester):
    here = pathlib.Path(__file__).resolve().parent.parent / "conftest.py"
    pytester.makeconftest(here.read_text(encoding="utf-8"))
    pytester.makepyfile(test_inner="""
        import socket

        def test_reaches_the_model_server():
            try:
                socket.create_connection(("127.0.0.1", 8000), timeout=1)
            except Exception:
                pass          # the code under test fails closed; the tripwire still fails the test
    """)
    result = pytester.runpytest_subprocess("-p", "no:cacheprovider")
    result.assert_outcomes(passed=1, errors=1)
    result.stdout.fnmatch_lines(["*network tripwire*127.0.0.1*8000*"])
