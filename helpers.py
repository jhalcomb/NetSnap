from datetime import datetime
from pathlib import Path
from getpass import getpass
from models import (
    Device,
    CommandResult,
    Credentials
)
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from threading import Event
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)
from report_builder.html import (
    create_device_html,
    create_toc,
)
from command_profiles import load_profile
from platform_detection import detect_platform

STOP_EVENT = Event()

# ----------------------------------------------------------------------
# SSH / Netmiko
# ----------------------------------------------------------------------

def get_inventory_credentials(
    ssh_creds: Credentials
):

    use_same = input(
        "Use same credentials for inventory? "
        "[Y/n] > "
    ).strip().lower()

    if use_same in ("", "y", "yes"):
        return ssh_creds

    return Credentials(
        username=input(
            "Inventory Username > "
        ),
        password=getpass(
            "Inventory Password > "
        )
    )

def collect_commands(
    device: Device,
    commands: list[str],
    username: str,
    password: str,
    netmiko_type: str,
) -> None:
    """SSH to one device and collect command output."""

    connection_params = {
        "device_type": netmiko_type,
        "host": device.ip,
        "username": username,
        "password": password,
        "fast_cli": False,
        "conn_timeout": 10,
        "auth_timeout": 10,
        "banner_timeout": 10,
    }

    print(
        f"Connecting to {device.hostname} "
        f"({device.ip}) [{device.platform}]"
    )

    with ConnectHandler(**connection_params) as connection:

        for command in commands:

            output = connection.send_command(
                command,
                read_timeout=120,
            )

            device.command_results.append(
                CommandResult(
                    command=command,
                    output=output,
                )
            )



def process_device(
    device: Device,
    username: str,
    password: str,
    output_path: Path,
):
    if STOP_EVENT.is_set():
        return None

    if not device.ip:
        raise ValueError(
            f"{device.hostname} has no IP"
        )

    print(
        f"Starting {device.hostname}"
    )


    platform_info = detect_platform(device)
    device.detected_os = platform_info.os_family
    device.detected_role = platform_info.role
    device.netmiko_driver = platform_info.netmiko_type
    device_commands = load_profile(platform_info.command_profile, platform_info.role)

    print(
        f"Detected {device.hostname}: {platform_info.os_family}, "
        f"{platform_info.role} "
        f"({platform_info.netmiko_type}, {platform_info.command_profile})"
    )

    collect_commands(
        device,
        device_commands,
        username,
        password,
        platform_info.netmiko_type,
    )

    if STOP_EVENT.is_set():
        return None

    filename = create_device_html(
        device,
        output_path,
    )

    return filename

# ----------------------------------------------------------------------
# Main collection orchestration
# ----------------------------------------------------------------------

def collect_device_outputs(
    devices: list[Device],
    username: str,
    password: str,
    max_workers: int = 5,
):

    STOP_EVENT.clear()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )


    output_path = (
        Path("SCRIPT_OUTPUTS")
        / timestamp
    )

    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_devices = len(devices)

    processed_count = 0
    successful = []
    failed = []
    filenames = []

    create_toc(
        output_path,
        filenames,
        failed,
        total_devices,
        processed_count,
    )

    executor = ThreadPoolExecutor(
        max_workers=max_workers
    )

    future_to_device = {}

    try:

        for device in devices:

            if STOP_EVENT.is_set():
                break

            future = executor.submit(
                process_device,
                device,
                username,
                password,
                output_path,
            )

            future_to_device[future] = device

        for future in as_completed(
            future_to_device
        ):

            device = future_to_device[
                future
            ]

            try:

                filename = future.result()

                if filename:

                    filenames.append(
                        filename
                    )

                    successful.append(
                        device.hostname
                    )

                    print(
                        f"[OK] "
                        f"{device.hostname}"
                    )

            except NetmikoAuthenticationException:

                failed.append(
                    {
                        "hostname": device.hostname,
                        "ip": device.ip,
                        "platform": device.platform,
                        "error": "Authentication failed",
                    }
                )

                print(
                    f"[FAIL] {device.hostname}: "
                    "Authentication failed"
                )

            except NetmikoTimeoutException:

                failed.append(
                    {
                        "hostname": device.hostname,
                        "ip": device.ip,
                        "platform": device.platform,
                        "error": "Connection timeout",
                    }
                )

                print(
                    f"[FAIL] {device.hostname}: "
                    "Connection timeout"
                )

            except Exception as error:

                failed.append(
                    {
                        "hostname": device.hostname,
                        "ip": device.ip,
                        "platform": device.platform,
                        "error": str(error),
                    }
                )

                print(
                    f"[FAIL] "
                    f"{device.hostname}: "
                    f"{error}"
                )

            processed_count += 1

            create_toc(
                output_path,
                filenames,
                failed,
                total_devices,
                processed_count,
            )

            print(
                f"[{processed_count}/"
                f"{total_devices}] "
                f"complete"
            )

    except KeyboardInterrupt:

        print()
        print(
            "Ctrl+C received. "
            "Stopping..."
        )

        STOP_EVENT.set()

        executor.shutdown(
            wait=False,
            cancel_futures=True,
        )

    finally:

        executor.shutdown(
            wait=False,
            cancel_futures=True,
        )

        create_toc(
            output_path,
            filenames,
            failed,
            total_devices,
            processed_count,
        )

        print()
        print("Summary")
        print("-------")

        print(
            f"Completed: "
            f"{processed_count}/"
            f"{total_devices}"
        )

        print(
            f"Successful: "
            f"{len(successful)}"
        )

        print(
            f"Failed: "
            f"{len(failed)}"
        )

        print()
        print(
            f"Reports saved to "
            f"{output_path.resolve()}"
        )

    return {
        "successful": successful,
        "failed": failed,
        "output_path": output_path,
    }