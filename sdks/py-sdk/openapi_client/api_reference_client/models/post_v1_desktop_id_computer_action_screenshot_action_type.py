from enum import Enum


class PostV1DesktopIdComputerActionScreenshotActionType(str, Enum):
    SCREENSHOT = "screenshot"

    def __str__(self) -> str:
        return str(self.value)
