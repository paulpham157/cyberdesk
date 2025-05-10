from enum import Enum


class PostV1DesktopIdComputerActionScrollActionDirection(str, Enum):
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"

    def __str__(self) -> str:
        return str(self.value)
