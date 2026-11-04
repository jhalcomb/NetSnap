from getpass import getpass
from inventory.catalyst_center import (CatalystCenterInventory)
from inventory.solarwinds import (SolarWindsInventory)
from models import Credentials
from helpers import (
    collect_device_outputs,
    get_inventory_credentials,
)


MAX_WORKERS = 5


INVENTORY_PROVIDERS = {
    "1": {
        "name": "Catalyst Center",
        "class": CatalystCenterInventory,
    },
    "2": {
        "name": "SolarWinds",
        "class": SolarWindsInventory,
    },
}


def get_inventory():

    print()
    print("Inventory Sources")
    print("-----------------")

    for key, info in (
        INVENTORY_PROVIDERS.items()
    ):

        print(
            f"{key}. {info['name']}"
        )

    print()

    return input(
        "Select inventory source (number): "
    ).strip()



def main():

    ssh_creds = Credentials(
        username=input("SSH Username > "),
        password=getpass("SSH Password > ")
    )

    choice = get_inventory()

    inventory_creds = (
    get_inventory_credentials(
        ssh_creds
        )
    )

    provider = INVENTORY_PROVIDERS.get(
        choice
    )

    if not provider:

        print(
            "Invalid inventory source."
        )
        return

    inventory = (
        provider["class"]
        .from_user_input(
            inventory_creds
        )
    )

    

    devices = inventory.get_devices()

    print(
        f"Retrieved "
        f"{len(devices)} devices "
        f"from {provider['name']}"
    )

    collect_device_outputs(
        devices,
        ssh_creds.username,
        ssh_creds.password,
        max_workers=MAX_WORKERS,
    )


if __name__ == "__main__":
    main()