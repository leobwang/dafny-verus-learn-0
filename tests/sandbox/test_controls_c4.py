"""sandbox/image/controls.py's C4 on an invented /sys/class/net (Δ506). Docker
Desktop's LinuxKit kernel puts its tunnel modules' fallback devices in every
network namespace, down and without an address; C4 ignores a down interface
only while the effective capability set has no CAP_NET_ADMIN, and lists it in
the detail and the record. No Docker: the interface tree and the route table
are files in a temporary directory."""

import importlib.machinery
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_loader = importlib.machinery.SourceFileLoader("dvl_controls", str(ROOT / "sandbox" / "image" / "controls.py"))
_spec = importlib.util.spec_from_loader("dvl_controls", _loader)
controls = importlib.util.module_from_spec(_spec)
_loader.exec_module(controls)

UP, DOWN = "0x1003", "0x80"           # IFF_UP set; a LinuxKit tunnel device's flags
NO_CAPS = 0
NET_ADMIN = 1 << 12
FALLBACK = ["erspan0", "gre0", "gretap0", "ip6_vti0", "ip6gre0", "ip6tnl0", "ip_vti0", "sit0", "tunl0"]


class C4(unittest.TestCase):
    def tree(self, ifaces, files=("bonding_masters",), routes=()):
        d = Path(self.enterContext(tempfile.TemporaryDirectory()))
        net = d / "net"
        net.mkdir()
        for name, flags in ifaces.items():
            (net / name).mkdir()
            (net / name / "flags").write_text(flags + "\n")
        for f in files:
            (net / f).write_text("\n")
        route = d / "route"
        route.write_text("Iface\tDestination\tGateway\n" + "".join(f"{i}\t{dst}\t0\n" for i, dst in routes))
        return str(net), str(route)

    def c4(self, ifaces, cap, network="none", **kw):
        net, route = self.tree(ifaces, **kw)
        return controls.c4({"network": network}, cap_eff=cap, net=net, route=route)

    def test_down_devices_without_net_admin_pass_and_are_listed(self):
        ok, detail, extra = self.c4({"lo": "0x9", **{n: DOWN for n in FALLBACK}}, NO_CAPS)
        self.assertTrue(ok, detail)
        self.assertEqual(extra, {"down": FALLBACK, "down_ignored": True})
        self.assertIn("interfaces ['lo']", detail)
        self.assertIn("down ['erspan0'", detail)

    def test_an_up_extra_interface_fails(self):
        ok, detail, extra = self.c4({"lo": "0x9", "eth0": UP}, NO_CAPS)
        self.assertFalse(ok, detail)
        self.assertIn("eth0", detail)

    def test_down_devices_with_net_admin_fail(self):
        ok, detail, extra = self.c4({"lo": "0x9", "tunl0": DOWN}, NET_ADMIN)
        self.assertFalse(ok, detail)
        self.assertEqual(extra, {"down": ["tunl0"], "down_ignored": False})
        self.assertIn("counted", detail)

    def test_down_devices_with_capeff_unknown_fail(self):
        net, route = self.tree({"lo": "0x9", "tunl0": DOWN})
        old = controls._status
        controls._status = lambda: {}
        try:
            ok, detail, _ = controls.c4({"network": "none"}, net=net, route=route)
        finally:
            controls._status = old
        self.assertFalse(ok, detail)

    def test_non_directory_entries_are_no_interfaces(self):
        ok, detail, extra = self.c4({"lo": "0x9"}, NET_ADMIN, files=("bonding_masters", "a-file"))
        self.assertTrue(ok, detail)
        self.assertEqual(extra["down"], [])
        self.assertNotIn("bonding_masters", detail)

    def test_a_route_still_fails(self):
        ok, detail, _ = self.c4({"lo": "0x9"}, NO_CAPS, routes=[("lo", "0100007F")])
        self.assertFalse(ok, detail)

    def test_the_model_network_counts_only_up_interfaces_without_net_admin(self):
        ifaces = {"lo": "0x9", "eth0": UP, **{n: DOWN for n in FALLBACK}}
        routes = [("eth0", "000013AC")]
        ok, detail, _ = self.c4(ifaces, NO_CAPS, network="model", routes=routes)
        self.assertTrue(ok, detail)
        ok, detail, _ = self.c4(ifaces, NET_ADMIN, network="model", routes=routes)
        self.assertFalse(ok, detail)
        ok, detail, _ = self.c4({"lo": "0x9", "eth0": UP, "eth1": UP}, NO_CAPS, network="model",
                                routes=routes)
        self.assertFalse(ok, detail)

    def test_check_puts_the_down_list_in_the_record(self):
        net, route = self.tree({"lo": "0x9", "sit0": DOWN})
        old = controls.c4
        controls.c4 = lambda req: old(req, cap_eff=NO_CAPS, net=net, route=route)
        try:
            rep = controls.check({"network": "none", "public": [], "public_name": "invalid."})
        finally:
            controls.c4 = old
        c4 = next(c for c in rep["controls"] if c["id"] == "C4")
        self.assertTrue(c4["ok"], c4)
        self.assertEqual(c4["down"], ["sit0"])
        self.assertTrue(c4["down_ignored"])


if __name__ == "__main__":
    unittest.main()
