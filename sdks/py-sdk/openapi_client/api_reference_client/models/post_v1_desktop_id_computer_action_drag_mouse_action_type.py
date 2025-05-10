from enum import Enum


class PostV1DesktopIdComputerActionDragMouseActionType(str, Enum):
    DRAG_MOUSE = "drag_mouse"

    def __str__(self) -> str:
        return str(self.value)
