from enum import Enum


class PostV1DesktopIdComputerActionTypeTextActionType(str, Enum):
    TYPE = "type"

    def __str__(self) -> str:
        return str(self.value)
