# NetSnap

NetSnap is a Python-based network data collection and reporting tool that retrieves device inventories from various sources, connects to devices over SSH, collects operational data, and generates browsable HTML reports.

## Features

- Multiple inventory providers
  - Cisco Catalyst Center
  - SolarWinds Orion
  - Additional providers can be added through the inventory framework

- SSH data collection
  - Concurrent device processing
  - Netmiko-based command execution
  - Platform-aware device handling

- HTML reporting
  - Searchable index page
  - Per-device report pages
  - Collapsible command output sections
  - Collection progress tracking
  - Successful, failed, and skipped device reporting

- Error handling
  - Authentication failures
  - Connection timeouts
  - Missing management IPs
  - Partial report generation if collection is interrupted

## Project Structure

```text
NetSnap/

inventory/
├── base.py
├── catalyst_center.py
└── solarwinds.py

report_builder/
└── html.py

html_templates/
├── device.html
└── toc.html

SCRIPT_OUTPUTS/
└── YYYY-MM-DD_HH-MM-SS/

main.py
helpers.py
models.py
```

## Requirements

- Python 3.11+
- Netmiko
- Cisco DNAC SDK (optional)
- Orion SDK (optional)
- Jinja2

Install dependencies:

```bash
pip install -r requirements.txt
```

## Inventory Providers

### Catalyst Center

Supports collecting inventories directly from Cisco Catalyst Center.

Example:

```text
Inventory Sources
-----------------
1. Catalyst Center
2. SolarWinds
```

When selected:

```text
Catalyst Center URL [default https://] >
```

### SolarWinds

Supports collecting inventories from SolarWinds Orion through SWIS.

Example:

```text
SolarWinds Server >
```

## Running NetSnap

```bash
python main.py
```

Example:

```text
SSH Username >
SSH Password >

Inventory Sources
-----------------
1. Catalyst Center
2. SolarWinds

Select inventory source >
```

Inventory credentials can optionally be different from SSH credentials.

## Platform detection

NetSnap centralizes platform detection in `platform_detection.py`. Every inventory
provider populates the `Device` model with the available platform, software,
and role metadata. `detect_platform(device)` returns:

- `os_family`: `ios`, `iosxe`, `nxos`, `iosxr`, `asa`, or `ftd`
- `netmiko_type`: SSH driver chosen **only** by the OS
- `role`: `router`, `switch`, `firewall`, or `unknown`, chosen from the inventory role,
  otherwise a conservative model-name heuristic
- `command_profile`: the OS-specific YAML file

Commands are defined under `commands:` (always collected) and optional
`role_commands.router:` / `role_commands.switch:` groups in the same YAML file.
When role is unknown, NetSnap still runs common commands such as `show ip route`.
Detected OS, role, and driver are also shown in each device HTML report.
Missing OS information is classified as Skipped (unsupported) rather than
assuming a potentially incorrect driver. An inventory's category is preferred over role guesses from the model.

Catalyst Center supplies `family`, `softwareType`, and `platformId`. SolarWinds
supplies `MachineType`, `IOSImage`, and `Description`; a model heuristic can fill
in router/switch when no explicit role is provided. Hardware series can be
ambiguous, so adjust the model rules or provide a trusted role when necessary.

Tests (no network connection required):

```bash
python -m unittest discover -s tests -v
```

## Generated Reports

Reports are written to:

```text
SCRIPT_OUTPUTS/
└── YYYY-MM-DD_HH-MM-SS/
```

Each report directory contains:

```text
index.html
Switch01_abcd123456.html
Switch02_123456abcd.html
Router01_abcdef1234.html
```

Open:

```text
index.html
```

to browse the report set.

## Failed and Skipped Devices

NetSnap tracks attempted-but-failed devices separately from inventory records
that are intentionally excluded or have unsupported platforms.

Examples:

- Authentication failed
- Connection timeout
- Missing management IP
- Unexpected exceptions

## Adding Inventory Sources

Implement the inventory interface:

```python
from inventory.base import InventoryBase

class MyInventory(InventoryBase):

    def get_devices(self):
        ...
```

Return a list of `Device` objects:

```python
Device(
    hostname="Switch01",
    ip="10.1.1.1",
    platform="C9300",
)
```

Register the provider in:

```python
INVENTORY_PROVIDERS
```

inside `main.py`.

## Roadmap

Possible enhancements:

- CSV inventory provider
- NetBox inventory provider
- Nautobot inventory provider
- JSON exports
- Parsed command output summaries
- Device health dashboards
- Configuration collection modules
- Additional SSH and API collectors

## License

MIT License

## ASA/FTD and Skipped devices

The central platform detector supports `asa` (`cisco_asa`) and `ftd`
(`cisco_ftd`) using separate read-only YAML command profiles:

- `command_profiles/cisco_asa.yaml` — `show version`, `show interface ip brief`,
  `show route`, `show failover`.
- `command_profiles/cisco_ftd.yaml` — `show version`, `show network`,
  `show managers`, `show time` from **FTD's top-level CLI**.

**Important:** A Firepower 1010/2130 model alone does not tell you whether
ASA or FTD software is installed. `platform_detection.FIREPOWER_DEFAULT_OS`
is set to `"ftd"` for convenience with SolarWinds records that provide only
`MachineType`. If that assumption is unsafe in your inventory, change it to
`None` to skip ambiguous hardware. Explicit `os_type="ASA"` or `"FTD"`
from the inventory overrides the hardware fallback. For ASA-imaged
Firepower hardware, supply the explicit OS to avoid a wrong Netmiko driver.

Skipped inventory records are listed **in orange at the bottom of the report**
with hostname, IP, platform, and reason. Deliberately excluded categories:
UCS, CUCM/Call Manager, VG/voice gateways, APIC, MCU; other unknown platforms
are also skipped instead of reported as SSH failures. A detected supported
platform that fails SSH/authentication/command collection is **Failed**.

Each successful report filename includes a stable hash of its hostname/IP/source,
so two devices that share a hostname do not overwrite each other's HTML files.

After collection, totals are: `successful + failed + skipped = processed`.

Run offline tests with `python -m unittest discover -s tests -v`.
