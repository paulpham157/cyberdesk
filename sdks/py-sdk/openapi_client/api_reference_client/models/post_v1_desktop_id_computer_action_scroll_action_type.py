from enum import Enum


class PostV1DesktopIdComputerActionScrollActionType(str, Enum):
    SCROLL = "scroll"

    def __str__(self) -> str:
        return str(self.value)
