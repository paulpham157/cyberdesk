from enum import Enum


class PostV1DesktopIdComputerActionClickMouseActionButton(str, Enum):
    LEFT = "left"
    MIDDLE = "middle"
    RIGHT = "right"

    def __str__(self) -> str:
        return str(self.value)
