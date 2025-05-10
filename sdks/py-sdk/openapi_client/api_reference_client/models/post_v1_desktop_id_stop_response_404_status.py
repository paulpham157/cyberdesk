from enum import Enum


class PostV1DesktopIdStopResponse404Status(str, Enum):
    ERROR = "error"

    def __str__(self) -> str:
        return str(self.value)
