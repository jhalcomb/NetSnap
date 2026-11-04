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

    command_results: list[CommandResult] = field(
        default_factory=list
    )


@dataclass
class Credentials:
    username: str
    password: str