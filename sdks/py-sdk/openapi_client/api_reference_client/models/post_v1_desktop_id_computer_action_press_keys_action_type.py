from enum import Enum


class PostV1DesktopIdComputerActionPressKeysActionType(str, Enum):
    PRESS_KEYS = "press_keys"

    def __str__(self) -> str:
        return str(self.value)
