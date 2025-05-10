from enum import Enum


class PostV1DesktopIdComputerActionClickMouseActionType(str, Enum):
    CLICK_MOUSE = "click_mouse"

    def __str__(self) -> str:
        return str(self.value)
