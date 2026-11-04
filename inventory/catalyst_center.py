from inventory.base import InventoryBase
from dnacentersdk import api

from models import Device


class CatalystCenterInventory(InventoryBase):

    def __init__(
        self,
        url,
        username,
        password,
        verify=False,
    ):
        self.dnac = api.DNACenterAPI(
            username=username,
            password=password,
            base_url=url,
            verify=verify,
        )

    @classmethod
    def from_user_input(
        cls,
        creds,
    ):

        url = input(
            "Catalyst Center URL "
            "[default https://] > "
        ).strip()

        if not url:

            raise ValueError(
                "URL cannot be blank."
            )

        if not url.startswith(
            ("http://", "https://")
        ):
            url = f"https://{url}"

        return cls(
            url=url,
            username=creds.username,
            password=creds.password,
        )


    def get_devices(
        self,
        page_size=500,
    ):
        families = [
            "Routers",
            "Switches and Hubs",
        ]

        device_objects = []

        for family in families:

            offset = 1

            while True:

                response = (
                    self.dnac.devices.get_device_list(
                        family=family,
                        limit=page_size,
                        offset=offset,
                    )
                )

                page = response.get(
                    "response",
                    []
                )

                if not page:
                    break

                for device in page:

                    device_objects.append(
                        Device(
                            hostname=device.get("hostname", "unknown"),
                            ip=device.get("managementIpAddress"),
                            platform=device.get("platformId", "UNKNOWN"),
                            os_type=device.get("softwareType"),
                            serial=device.get("serialNumber", ""),
                            role=device.get("family"),
                            source="Catalyst Center",
                        )
                    )

                if len(page) < page_size:
                    break

                offset += page_size


        return device_objects