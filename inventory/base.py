from abc import ABC, abstractmethod


class InventoryBase(ABC):

    @abstractmethod
    def get_devices(self):
        pass
