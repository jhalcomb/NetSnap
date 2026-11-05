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
  - Failed device reporting

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

report_generators/
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

- `os_family`: `ios`, `iosxe`, `nxos`, or `iosxr`
- `netmiko_type`: SSH driver chosen **only** by the OS
- `role`: `router`, `switch`, or `unknown`, chosen from the inventory role,
  otherwise a conservative model-name heuristic
- `command_profile`: the OS-specific YAML file

Commands are defined under `commands:` (always collected) and optional
`role_commands.router:` / `role_commands.switch:` groups in the same YAML file.
When role is unknown, NetSnap still runs common commands such as `show ip route`.
Detected OS, role, and driver are also shown in each device HTML report.
Missing OS information still causes a clear error rather than an unsafe driver
fallback. An inventory's category is preferred over role guesses from the model.

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
reports/
└── 2026-11-04_16-30-00/
```

Each report directory contains:

```text
index.html
Switch01.html
Switch02.html
Router01.html
```

Open:

```text
index.html
```

to browse the report set.

## Failed Devices

NetSnap tracks devices that could not be collected and includes them in the report.

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

## Platform detection (OS-only)

NetSnap resolves the network operating system from inventory metadata or a
known model family. This selects the Netmiko driver and one command profile
per OS; router/switch roles do **not** influence command selection.

| OS | Netmiko driver | Command profile |
|---|---|---|
| IOS / IOS XE | `cisco_ios` | `cisco_ios.yaml` |
| NX-OS | `cisco_nxos` | `cisco_nexus.yaml` |
| IOS XR | `cisco_xr` | `cisco_iosxr.yaml` |

The IOS/IOS XE profile intentionally includes routing and switching commands.
Some commands may be unsupported on a particular device and return CLI error
text; this is not a connection failure. Unknown platforms are rejected rather
than silently assumed to be IOS.
