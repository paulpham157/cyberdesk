from enum import Enum


class PostV1DesktopIdComputerActionWaitActionType(str, Enum):
    WAIT = "wait"

    def __str__(self) -> str:
        return str(self.value)
