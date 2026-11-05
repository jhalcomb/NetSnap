"""Offline reporting tests; no live device or Netmiko dependency."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from models import Device
from report_builder.html import create_device_html, create_toc


class HtmlReportTests(unittest.TestCase):
    def test_same_hostname_different_ips_have_distinct_reports(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            a = Device(hostname="FW", ip="192.0.2.10", platform="ASA", source="SolarWinds")
            b = Device(hostname="FW", ip="192.0.2.11", platform="ASA", source="SolarWinds")
            fa = create_device_html(a, root)
            fb = create_device_html(b, root)
            self.assertNotEqual(fa, fb)
            self.assertTrue((root / fa).exists())
            self.assertTrue((root / fb).exists())
            self.assertNotEqual(fa, "index.html")

    def test_index_renders_skipped_in_orange_at_bottom(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            report = create_toc(
                root,
                [{"filename": "FW_a.html", "hostname": "FW", "ip": "192.0.2.10"}],
                [{"hostname": "Fail", "ip": "192.0.2.11", "platform": "Nexus", "error": "Authentication failed"}],
                [{"hostname": "VG1", "ip": "192.0.2.12", "platform": "VG350", "reason": "Excluded: voice gateway"}],
                3,
                3,
            )
            html = report.read_text()
            self.assertIn('class="skipped-device"', html)
            self.assertIn('background-color: #fff2df;', html)
            self.assertTrue(html.index('<h2>Skipped Devices</h2>') > html.index('<h2>Failed Devices</h2>'))
            self.assertIn('Excluded: voice gateway', html)
            self.assertIn('id="skipped-count">1', html)
            self.assertIn('href="FW_a.html"', html)


if __name__ == '__main__':
    unittest.main()
