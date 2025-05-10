from enum import Enum


class PostV1DesktopIdComputerActionMoveMouseActionType(str, Enum):
    MOVE_MOUSE = "move_mouse"

    def __str__(self) -> str:
        return str(self.value)
