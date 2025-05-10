from enum import Enum


class PostV1DesktopIdComputerActionResponse500Status(str, Enum):
    ERROR = "error"

    def __str__(self) -> str:
        return str(self.value)
