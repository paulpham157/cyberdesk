from .types import (
    PostV1DesktopIdComputerActionClickMouseAction,
    PostV1DesktopIdComputerActionDragMouseAction,
    PostV1DesktopIdComputerActionGetCursorPositionAction,
    PostV1DesktopIdComputerActionMoveMouseAction,
    PostV1DesktopIdComputerActionPressKeysAction,
    PostV1DesktopIdComputerActionScreenshotAction,
    PostV1DesktopIdComputerActionScrollAction,
    PostV1DesktopIdComputerActionTypeTextAction,
    PostV1DesktopIdComputerActionWaitAction,
)

def click_mouse(x: int, y: int, button: str = "left") -> PostV1DesktopIdComputerActionClickMouseAction:
    return PostV1DesktopIdComputerActionClickMouseAction(type="click_mouse", x=x, y=y, button=button)

def drag_mouse(start_x: int, start_y: int, end_x: int, end_y: int, button: str = "left") -> PostV1DesktopIdComputerActionDragMouseAction:
    return PostV1DesktopIdComputerActionDragMouseAction(type="drag_mouse", start_x=start_x, start_y=start_y, end_x=end_x, end_y=end_y, button=button)

def get_cursor_position() -> PostV1DesktopIdComputerActionGetCursorPositionAction:
    return PostV1DesktopIdComputerActionGetCursorPositionAction(type="get_cursor_position")

def move_mouse(x: int, y: int) -> PostV1DesktopIdComputerActionMoveMouseAction:
    return PostV1DesktopIdComputerActionMoveMouseAction(type="move_mouse", x=x, y=y)

def press_keys(keys: list[str]) -> PostV1DesktopIdComputerActionPressKeysAction:
    return PostV1DesktopIdComputerActionPressKeysAction(type="press_keys", keys=keys)

def screenshot() -> PostV1DesktopIdComputerActionScreenshotAction:
    return PostV1DesktopIdComputerActionScreenshotAction(type="screenshot")

def scroll(dx: int, dy: int) -> PostV1DesktopIdComputerActionScrollAction:
    return PostV1DesktopIdComputerActionScrollAction(type="scroll", dx=dx, dy=dy)

def type_text(text: str) -> PostV1DesktopIdComputerActionTypeTextAction:
    return PostV1DesktopIdComputerActionTypeTextAction(type="type", text=text)

def wait(ms: int) -> PostV1DesktopIdComputerActionWaitAction:
    return PostV1DesktopIdComputerActionWaitAction(type="wait", ms=ms) 