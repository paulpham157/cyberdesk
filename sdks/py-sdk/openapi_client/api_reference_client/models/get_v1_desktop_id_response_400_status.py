from enum import Enum


class GetV1DesktopIdResponse400Status(str, Enum):
    ERROR = "error"

    def __str__(self) -> str:
        return str(self.value)
