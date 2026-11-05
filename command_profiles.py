"""Load OS command profiles with optional router/switch additions."""

from pathlib import Path
import yaml

from models import Device
from platform_detection import detect_platform

PROFILE_DIR = Path(__file__).parent / "command_profiles"
ROLES = {"router", "switch", "firewall", "unknown"}


def determine_profile(device: Device) -> str:
    return detect_platform(device).command_profile


def load_profile(profile_name: str, role: str = "unknown") -> list[str]:
    """Merge common commands and role-specific commands without duplicates."""
    if role not in ROLES:
        raise ValueError(f"Unsupported device role: {role!r}")

    # Avoid accepting paths from external/inventory data.
    profile_file = PROFILE_DIR / f"{profile_name}.yaml"
    if profile_file.name != f"{profile_name}.yaml":
        raise ValueError(f"Invalid command profile: {profile_name!r}")

    with profile_file.open("r", encoding="utf-8") as file:
        profile = yaml.safe_load(file)

    if not isinstance(profile, dict):
        raise ValueError(f"Invalid YAML profile {profile_file.name}")

    role_commands = profile.get("role_commands", {})
    if not isinstance(role_commands, dict):
        raise ValueError(f"Invalid role_commands in {profile_file.name}")
    common = profile.get("commands")
    extra = role_commands.get(role, [])
    if not isinstance(common, list) or not isinstance(extra, list):
        raise ValueError(f"Commands must be lists in {profile_file.name}")
    commands = common + extra
    if not all(isinstance(command, str) and command.strip() for command in commands):
        raise ValueError(f"Commands must be nonempty strings in {profile_file.name}")

    return list(dict.fromkeys(commands))


def get_commands_for_device(device: Device) -> list[str]:
    platform_info = detect_platform(device)
    return load_profile(platform_info.command_profile, platform_info.role)
