"""Run with: python -m unittest discover -s tests -v"""
import unittest

from models import Device
from platform_detection import DeviceSkipped, detect_platform
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


    def test_solarwinds_image_names_and_platforms(self):
        # Examples taken from the SolarWinds operational report.
        cases = [
            ("Cisco Catalyst 29xxStack", "C2960S-UNIVERSALK9-M", "ios", "switch"),
            ("Catalyst 37xx Stack", "C3750-IPSERVICESK9-M", "ios", "switch"),
            ("Cisco Catalyst 38xx stack", "CAT3K_CAA-UNIVERSALK9-M", "iosxe", "switch"),
            ("Cisco 2921K9", "C2900-UNIVERSALK9-M", "ios", "router"),
            ("Catalyst 8300-1N1S-6T", "X86_64_LINUX_IOSD-UNIVERSALK9-M", "iosxe", "router"),
            ("Cisco Catalyst C8300-1N1S-4T2X", "X86_64_LINUX_IOSD-UNIVERSALK9-M", "iosxe", "router"),
            ("Cisco 4431 ISR", "X86_64_LINUX_IOSD-UNIVERSALK9-M", "iosxe", "router"),
            ("Cisco 4331 ISR", "X86_64_LINUX_IOSD-UNIVERSALK9-M", "iosxe", "router"),
        ]
        for model, image, expected_os, expected_role in cases:
            with self.subTest(model=model):
                info = detect_platform(dev("SolarWindsNode", model, image))
                self.assertEqual(info.os_family, expected_os)
                self.assertEqual(info.role, expected_role)
                self.assertEqual(info.netmiko_type, "cisco_ios")

    def test_intentionally_skipped_devices(self):
        examples = [
            ("Cisco UCS C240 M5", "UCS"),
            ("Cisco Unified Communications Manager", "Call Manager"),
            ("APIC Server M2", "APIC"),
            ("Cisco MCU 4505", "MCU"),
            ("VG310", "voice gateway"),
            ("VG350", "voice gateway"),
            ("Cisco VG450 Analog Voice Gateway", "voice gateway"),
        ]
        for model, reason in examples:
            with self.subTest(model=model):
                with self.assertRaisesRegex(DeviceSkipped, reason):
                    # Even an IOS image shouldn't override explicit exclusions.
                    detect_platform(dev("Device", model, "IOS XE"))

    def test_asa_and_ftd_supported(self):
        examples = [
            ("Cisco ASA 5505", None, "asa", "cisco_asa"),
            ("Cisco ASA 5512-X", None, "asa", "cisco_asa"),
            ("Firepower 2130", None, "ftd", "cisco_ftd"),
            ("Cisco FirePOWER 1010 Security Appliance", None, "ftd", "cisco_ftd"),
            ("Firepower 2130", "ASA", "asa", "cisco_asa"),
            ("Firepower 2130", "FTD", "ftd", "cisco_ftd"),
            ("Cisco ASA 5512-X", "FTD", "ftd", "cisco_ftd"),
        ]
        for model, os_type, expected_os, expected_driver in examples:
            with self.subTest(model=model, os_type=os_type):
                result = detect_platform(dev("FW", model, os_type))
                self.assertEqual(result.os_family, expected_os)
                self.assertEqual(result.netmiko_type, expected_driver)
                self.assertEqual(result.command_profile, f"cisco_{expected_os}")
                self.assertEqual(result.role, "firewall")

        self.assertIn("show route", load_profile("cisco_asa", "firewall"))
        self.assertIn("show network", load_profile("cisco_ftd", "firewall"))
        self.assertNotIn("system support diagnostic-cli", load_profile("cisco_ftd", "firewall"))

    def test_ambiguous_firepower_can_be_skipped(self):
        from unittest.mock import patch
        with patch("platform_detection.FIREPOWER_DEFAULT_OS", None):
            with self.assertRaisesRegex(DeviceSkipped, "ambiguous"):
                detect_platform(dev("FW", "Firepower 2130"))

    def test_unknown_os_skipped_not_failed(self):
        device = dev("Unknown", "Mystery 123")
        with self.assertRaisesRegex(DeviceSkipped, "Unsupported"):
            detect_platform(device)

    def test_profiles_for_all_platforms(self):
        for name in ("cisco_ios", "cisco_nexus", "cisco_iosxr", "cisco_asa", "cisco_ftd"):
            for role in ("router", "switch", "unknown"):
                with self.subTest(profile=name, role=role):
                    self.assertTrue(load_profile(name, role))


if __name__ == "__main__":
    unittest.main()
