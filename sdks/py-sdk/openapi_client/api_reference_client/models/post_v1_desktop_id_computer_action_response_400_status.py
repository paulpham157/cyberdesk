from enum import Enum


class PostV1DesktopIdComputerActionResponse400Status(str, Enum):
    ERROR = "error"

    def __str__(self) -> str:
        return str(self.value)
