from dataclasses import dataclass, field

@dataclass
class CommandResult:
    command: str
    output: str


@dataclass
class Device:
    hostname: str
    ip: str | None
    platform: str
    os_type: str | None = None

    serial: str | None = None
    role: str | None = None
    source: str = ""
    description: str | None = None

    # Populated after centralized platform classification.
    detected_os: str | None = None
    detected_role: str | None = None
    netmiko_driver: str | None = None

    command_results: list[CommandResult] = field(
        default_factory=list
    )


@dataclass
class Credentials:
    username: str
    password: str