from enum import Enum


class PostV1DesktopIdComputerActionPressKeysActionKeyActionType(str, Enum):
    DOWN = "down"
    PRESS = "press"
    UP = "up"

    def __str__(self) -> str:
        return str(self.value)
