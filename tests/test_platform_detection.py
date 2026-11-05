"""Run with: python -m unittest discover -s tests -v"""
import unittest

from models import Device
from platform_detection import detect_platform
from command_profiles import load_profile, get_commands_for_device


def dev(hostname, model, os_type=None, role=None, description=None):
    return Device(
        hostname=hostname, ip="192.0.2.1", platform=model,
        os_type=os_type, role=role, description=description,
    )


class PlatformDetectionTests(unittest.TestCase):
    def test_cisco_models(self):
        scenarios = [
            (dev("Cat9300", "C9300-48P", "IOS-XE", "Switches and Hubs"),
             "cisco_ios", "cisco_ios", "switch"),
            (dev("ISR4331", "ISR4331/K9", "IOS XE", "Routers"),
             "cisco_ios", "cisco_ios", "router"),
            (dev("Nexus9k", "N9K-C93180", "NX-OS"),
             "cisco_nxos", "cisco_nexus", "switch"),
            (dev("ASR9k", "ASR-9006", "IOS-XR"),
             "cisco_xr", "cisco_iosxr", "router"),
            (dev("OldCat", "Cisco Catalyst 2960-X", description="Cisco IOS Software"),
             "cisco_ios", "cisco_ios", "switch"),
            (dev("IOSGeneric", "UNKNOWN", "Cisco IOS XE Software"),
             "cisco_ios", "cisco_ios", "unknown"),
            (dev("Cat8000", "C8000V", "IOS XE"),
             "cisco_ios", "cisco_ios", "router"),
        ]
        for device, driver, profile, role in scenarios:
            with self.subTest(hostname=device.hostname):
                result = detect_platform(device)
                self.assertEqual(result.netmiko_type, driver)
                self.assertEqual(result.command_profile, profile)
                self.assertEqual(result.role, role)

    def test_explicit_inventory_role_preferred(self):
        device = dev("Core", "UNKNOWN", "IOS XE", "Switches and Hubs")
        self.assertEqual(detect_platform(device).role, "switch")
        device.role = "Routers"
        self.assertEqual(detect_platform(device).role, "router")

    def test_ambiguous_role_falls_back_to_model(self):
        device = dev("Core", "ISR4331/K9", "IOS XE", "Router/Switch")
        self.assertEqual(detect_platform(device).role, "router")

    def test_role_does_not_change_netmiko_type(self):
        for role in ("Routers", "Switches and Hubs", None):
            with self.subTest(role=role):
                device = dev("Test", "UNKNOWN", "IOS XE", role)
                self.assertEqual(detect_platform(device).netmiko_type, "cisco_ios")

    def test_unknown_role_still_collects_common_commands(self):
        device = dev("Mystery", "UNKNOWN", "IOS XE")
        commands = get_commands_for_device(device)
        self.assertIn("show ip route", commands)
        self.assertNotIn("show switch", commands)

    def test_router_vs_switch_commands(self):
        router = get_commands_for_device(dev("Router", "ISR4331", "IOS XE"))
        switch = get_commands_for_device(dev("Switch", "C9300", "IOS XE"))
        for commands in (router, switch):
            self.assertIn("show ip route", commands)
            self.assertIn("show inventory", commands)
            self.assertEqual(len(commands), len(set(commands)))
        self.assertIn("show ip bgp summary", router)
        self.assertNotIn("show switch", router)
        self.assertIn("show switch", switch)
        self.assertNotIn("show ip bgp summary", switch)

    def test_unknown_os_fails_instead_of_guessing(self):
        device = dev("Unknown", "Mystery 123")
        with self.assertRaisesRegex(ValueError, "Cannot detect OS"):
            detect_platform(device)

    def test_profiles_for_all_platforms(self):
        for name in ("cisco_ios", "cisco_nexus", "cisco_iosxr"):
            for role in ("router", "switch", "unknown"):
                with self.subTest(profile=name, role=role):
                    self.assertTrue(load_profile(name, role))


if __name__ == "__main__":
    unittest.main()
