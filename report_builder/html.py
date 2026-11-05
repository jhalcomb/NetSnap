from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from models import Device
import hashlib
import re


TEMPLATE_DIR = (
    Path(__file__).parent.parent
    / "html_templates"
)

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=True,
)

device_template = jinja_env.get_template("device.html")
toc_template = jinja_env.get_template("toc.html")


def safe_filename(hostname: str) -> str:
    """Convert hostname into a filesystem-safe name."""

    return re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        hostname,
    )


def create_device_html(
    device: Device,
    output_path: Path,
) -> str:
    """Create the HTML report for one device."""

    # Use identity rather than hostname alone: SolarWinds can return two
    # different devices with identical names (e.g. ASA HA peers).
    identity = f"{device.source}|{device.hostname.lower()}|{device.ip or ''}"
    suffix = hashlib.sha256(identity.encode('utf-8')).hexdigest()[:10]
    filename = f"{safe_filename(device.hostname)[:110]}_{suffix}.html"

    output_file = output_path / filename

    content = device_template.render(
        d=device,
    )

    output_file.write_text(
        content,
        encoding="utf-8",
    )

    return filename

def create_toc(
    output_path: Path,
    successful_devices: list[dict],
    failed_devices: list[dict],
    skipped_devices: list[dict],
    total_devices: int,
    processed_count: int,
) -> Path:
    """Create or update the table-of-contents page."""

    successful_devices = sorted(
        successful_devices, key=lambda d: (d["hostname"].lower(), d["ip"] or "")
    )

    content = toc_template.render(
        successful_devices=successful_devices,
        failed_devices=sorted(failed_devices, key=lambda d: d["hostname"].lower()),
        skipped_devices=sorted(skipped_devices, key=lambda d: d["hostname"].lower()),
        total_devices=total_devices,
        processed_count=processed_count,
    )

    toc_file = output_path / "index.html"

    toc_file.write_text(
        content,
        encoding="utf-8",
    )

    return toc_file