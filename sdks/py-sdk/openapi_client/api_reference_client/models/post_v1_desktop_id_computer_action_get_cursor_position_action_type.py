from enum import Enum


class PostV1DesktopIdComputerActionGetCursorPositionActionType(str, Enum):
    GET_CURSOR_POSITION = "get_cursor_position"

    def __str__(self) -> str:
        return str(self.value)
