from orionsdk import SwisClient

from inventory.base import InventoryBase
from models import Device


class SolarWindsInventory(InventoryBase):

    def __init__(
        self,
        hostname,
        username,
        password,
    ):
        self.swis = SwisClient(
            hostname,
            username,
            password,
        )


    @classmethod
    def from_user_input(
        cls,
        creds):

        hostname = input("SolarWinds Server > ")

        return cls(
            hostname=hostname,
            username=creds.username,
            password=creds.password,
        )

    def get_devices(self):

        query = """
        SELECT
            N.Caption,
            N.IPAddress,
            N.MachineType,
            N.Vendor,
            N.IOSImage,
            N.Status,
            N.SysName,
            N.NodeID,
            N.ObjectSubType
        FROM Orion.Nodes N
        WHERE N.Vendor LIKE '%Cisco%'
        """

        rows = self.swis.query(
            query
        )["results"]

        devices = []

        for row in rows:

            devices.append(
                Device(
                    hostname=row["Caption"],
                    ip=row["IPAddress"],
                    platform=row["MachineType"],
                    source="SolarWinds",
                )
            )

        return devices