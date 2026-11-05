"""Centralized Cisco OS and device-role detection.

OS selects the Netmiko driver. Router/switch role selects optional
supplemental show commands, never the SSH driver. Unknown roles are fine.
"""

from dataclasses import dataclass
import re

from models import Device


@dataclass(frozen=True)
class PlatformInfo:
    os_family: str
    netmiko_type: str
    command_profile: str
    role: str  # "router", "switch", or "unknown"


NETMIKO_DRIVERS = {
    "ios": "cisco_ios",
    "iosxe": "cisco_ios",
    "nxos": "cisco_nxos",
    "iosxr": "cisco_xr",
}

COMMAND_PROFILES = {
    "ios": "cisco_ios",
    "iosxe": "cisco_ios",
    "nxos": "cisco_nexus",
    "iosxr": "cisco_iosxr",
}


def _normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _os_from_software(value: str | None) -> str | None:
    text = _normalize(value)
    if re.search(r"\b(?:nx\s*os|nxos)\b", text):
        return "nxos"
    if re.search(r"\b(?:ios\s*xr|iosxr)\b", text):
        return "iosxr"
    if re.search(r"\b(?:ios\s*xe|iosxe)\b", text):
        return "iosxe"
    if re.search(r"\bios\b", text):
        return "ios"

    # SolarWinds Orion.Nodes.IOSImage is usually an *image identifier*,
    # not a friendly OS name. These patterns are for recognizable Cisco
    # image families. Don't classify a device from UNIVERSALK9 alone.
    if re.search(r"\b(?:x86\s*64\s*linux\s*iosd|cat3k\s*caa|cat9k\s*iosxe)\b", text):
        return "iosxe"
    if re.search(r"\b(?:c2960[a-z0-9]*|c3750[a-z0-9]*|c2900|vg3x0|vg310|vg350)\b", text):
        return "ios"
    return None


def _detect_os(device: Device) -> str | None:
    # Inventory software information is preferable to a model guess.
    for value in (device.os_type, device.description):
        if match := _os_from_software(value):
            return match

    model = _normalize(device.platform)

    # Conservative fallbacks for model families with a known OS.
    if "nexus" in model or re.search(r"\bn[3579]k\b", model):
        return "nxos"
    if re.search(r"\b(?:asr\s*9(?:00[016]|9\d{2})|xrv?\d*)\b", model):
        return "iosxr"
    if (
        # The Catalyst 8000 edge family and ISR 43xx/44xx run IOS XE.
        re.search(r"\b(?:catalyst\s+c?83\d{2}|c83\d{2}|(?:43|44)\d{2}\s*isr|vg450)\b", model)
        or re.search(r"\bc9\d{3}\b", model)
        or re.search(r"\bcatalyst\s+9\d{3}\b", model)
        or re.search(r"\bc(?:3650|3850)\b", model)
        or re.search(r"\b(?:isr\s*4\d{3}|asr\s*1\d{3}|csr\s*1000v|c8kv|c8000v)\b", model)
    ):
        return "iosxe"
    if (
        # SolarWinds sometimes reports a generic stack family rather than
        # a specific chassis model.
        re.search(r"\bcatalyst\s+(?:29xx|37xx)\s*stack\b", model)
        or re.search(r"\b(?:cisco\s+)?2921k9\b", model)
        or re.search(r"\b(?:vg310|vg350|vg3x0)\b", model)
        or re.search(r"\bc(?:2960|3560|3750)[a-z0-9]*\b", model)
        or re.search(r"\bcatalyst\s+(?:2960|3560|3750)\b", model)
    ):
        return "ios"
    return None


def _detect_role(device: Device) -> str:
    """Use inventory family/role first, then a conservative model fallback.

    Do not guess 'switch' merely because a device uses IOS XE: IOS XE runs
    on routers too. Both roles are intentionally allowed to be unknown.
    """
    inventory_role = _normalize(device.role)
    is_router = bool(re.search(r"\brouters?\b", inventory_role))
    is_switch = bool(re.search(r"\bswitch(?:es)?\b", inventory_role))
    if is_router != is_switch:
        return "router" if is_router else "switch"

    model = _normalize(device.platform)
    # Router hardware / virtual-router families.
    if (
        re.search(r"\b(?:isr|asr|csr)\b", model)
        or re.search(r"\b(?:isr|asr|csr)\d", model)
        or re.search(r"\b(?:c8kv|c8000v|xrv\d*|xr\d*)\b", model)
        or re.search(r"\bcatalyst\s+c?8\d{3}\b", model)
        or re.search(r"\b(?:43|44)\d{2}\s*isr\b", model)
        or re.search(r"\b(?:cisco\s+)?2921k9\b", model)
    ):
        return "router"

    # Physical switch families (including L3 switches).
    if (
        "nexus" in model
        or re.search(r"\bn[3579]k\b", model)
        or re.search(r"\bc9\d{3}\b", model)
        or re.search(r"\bc(?:1000|2960|3560|3650|3750|3850)[a-z0-9]*\b", model)
        or re.search(r"\bcatalyst\s+(?:1\d{3}|2\d{3}|3\d{3}|9\d{3})\b", model)
        or re.search(r"\bcatalyst\s+(?:29xx|37xx|38xx)\s*stack\b", model)
        or re.search(r"\bws\s*c(?:2\d{3}|3\d{3})\b", model)
    ):
        return "switch"

    # E.g. "Cisco 3925" alone may not be sufficiently unambiguous.
    return "unknown"


def detect_platform(device: Device) -> PlatformInfo:
    """Resolve platform info once per device, before selecting commands."""
    os_family = _detect_os(device)
    if os_family is None:
        raise ValueError(
            f"Cannot detect OS for {device.hostname}: "
            f"platform={device.platform!r}, os_type={device.os_type!r}, "
            f"description={device.description!r}"
        )

    return PlatformInfo(
        os_family=os_family,
        netmiko_type=NETMIKO_DRIVERS[os_family],
        command_profile=COMMAND_PROFILES[os_family],
        role=_detect_role(device),
    )
