"""The network tripwire for every harness test run (DV4-PLAN §9; frozen, guard rule 2f).

CI never calls a model, never starts a container and never connects outside
its own fakes. For the whole test session this file replaces socket
connection: a connection (TCP, UDP or a Unix socket) to any address that a
test's fake server has not registered, and any name lookup other than
localhost or a numeric address, is refused and fails the test loudly, even
when the code under test catches the error. So a test that reaches the live
Ollama on 127.0.0.1:11434, the Anthropic API, a container socket or any other
address fails.

A fake server registers its address for the test that uses it:

    def test_backend(net_allow):
        server = start_fake_ollama()            # binds 127.0.0.1:0
        net_allow(server.server_address)        # ("127.0.0.1", port), or a socket path
        ...

`net_trips` lists the refusals recorded in the current test; a test that
expects one asserts on the list and clears it (the tripwire's own tests do).
Child processes are outside this file's reach: the CI job runs them with a
sterile HOME, XDG and CLAUDE_CONFIG_DIR, FVH_NO_MODEL=1, DVL_NO_DOCKER=1 and
shims for claude, opencode, ollama, docker and sudo on PATH (scripts/ci.sh).
"""

import ipaddress
import socket

import pytest

_ALLOWED = set()
_TRIPS = []
_REAL = {}


class NetworkTripwire(RuntimeError):
    """A test reached for the network outside its registered fakes."""


def _key(family, address):
    if family == getattr(socket, "AF_UNIX", None):
        return ("unix", address.decode() if isinstance(address, bytes) else str(address))
    if isinstance(address, tuple) and len(address) >= 2:
        host, port = address[0], address[1]
        try:
            host = str(ipaddress.ip_address(host))
        except ValueError:
            host = str(host)
        return ("inet", host, int(port))
    return ("other", repr(address))


def _trip(what):
    _TRIPS.append(what)
    raise NetworkTripwire(f"network tripwire: {what} (CI never connects outside its own fakes; "
                          "register a fake server's address with the net_allow fixture)")


def _check(sock, address):
    k = _key(sock.family, address)
    if k not in _ALLOWED:
        _trip(f"a connection to {address!r}")


def _connect(self, address):
    _check(self, address)
    return _REAL["connect"](self, address)


def _connect_ex(self, address):
    _check(self, address)
    return _REAL["connect_ex"](self, address)


def _sendto(self, data, *args):
    address = args[-1]
    _check(self, address)
    return _REAL["sendto"](self, data, *args)


def _getaddrinfo(host, *args, **kwargs):
    if host not in (None, "", "localhost", b"localhost"):
        h = host.decode() if isinstance(host, bytes) else str(host)
        try:
            ipaddress.ip_address(h)
        except ValueError:
            _trip(f"a name lookup of {h!r}")
    return _REAL["getaddrinfo"](host, *args, **kwargs)


def pytest_configure(config):
    if _REAL:
        return
    _REAL.update(connect=socket.socket.connect, connect_ex=socket.socket.connect_ex,
                 sendto=socket.socket.sendto, getaddrinfo=socket.getaddrinfo)
    socket.socket.connect = _connect
    socket.socket.connect_ex = _connect_ex
    socket.socket.sendto = _sendto
    socket.getaddrinfo = _getaddrinfo


def pytest_unconfigure(config):
    if not _REAL:
        return
    socket.socket.connect = _REAL["connect"]
    socket.socket.connect_ex = _REAL["connect_ex"]
    socket.socket.sendto = _REAL["sendto"]
    socket.getaddrinfo = _REAL["getaddrinfo"]
    _REAL.clear()


@pytest.fixture
def net_allow():
    """Register a fake server's address for this test: a (host, port) tuple
    or a Unix socket path."""
    added = []

    def allow(address):
        family = getattr(socket, "AF_UNIX", None) if isinstance(address, (str, bytes)) else socket.AF_INET
        k = _key(family, address)
        _ALLOWED.add(k)
        added.append(k)
        return address

    yield allow
    for k in added:
        _ALLOWED.discard(k)


@pytest.fixture
def net_trips():
    """The refusals recorded in this test (a test that expects one clears it)."""
    return _TRIPS


@pytest.fixture(autouse=True)
def _network_tripwire():
    _TRIPS.clear()
    yield
    if _TRIPS:
        what = "; ".join(_TRIPS)
        _TRIPS.clear()
        pytest.fail(f"network tripwire: this test reached for the network outside its fakes: {what}",
                    pytrace=False)
