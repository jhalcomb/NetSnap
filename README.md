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