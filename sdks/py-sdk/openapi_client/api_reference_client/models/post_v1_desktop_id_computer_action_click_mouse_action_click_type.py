from enum import Enum


class PostV1DesktopIdComputerActionClickMouseActionClickType(str, Enum):
    CLICK = "click"
    DOWN = "down"
    UP = "up"

    def __str__(self) -> str:
        return str(self.value)
