from pathlib import Path

import yaml

from models import Device


PROFILE_DIR = (
    Path(__file__).parent
    / "command_profiles"
)

def determine_profile(
    device: Device,
) -> str:

    os_type = (
        device.os_type or ""
    ).lower()

    platform = (
        device.platform or ""
    ).lower()

    if "nx-os" in os_type:
        return "cisco_nexus"

    if "ios xr" in os_type:
        return "cisco_iosxr"

    if device.role:

        role = device.role.lower()

        if "router" in role:
            return "cisco_catalyst_router"

    return "cisco_catalyst_switch"

def load_profile(
    profile_name: str,
) -> list[str]:

    profile_file = (
        PROFILE_DIR
        / f"{profile_name}.yaml"
    )

    with open(
        profile_file,
        "r",
        encoding="utf-8"
    ) as file:

        profile = yaml.safe_load(
            file
        )

    return profile["commands"]

def get_commands_for_device(
    device: Device,
) -> list[str]:

    profile = determine_profile(
        device
    )

    return load_profile(
        profile
    )