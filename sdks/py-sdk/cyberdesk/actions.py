from typing import Union, List, Optional

from openapi_client.api_reference_client.types import UNSET
from openapi_client.api_reference_client.models import (
    PostV1DesktopIdComputerActionClickMouseAction,
    PostV1DesktopIdComputerActionClickMouseActionType,
    PostV1DesktopIdComputerActionClickMouseActionButton as ClickMouseButton,
    PostV1DesktopIdComputerActionClickMouseActionClickType as ClickMouseActionType,
    PostV1DesktopIdComputerActionDragMouseAction,
    PostV1DesktopIdComputerActionDragMouseActionType,
    PostV1DesktopIdComputerActionDragMouseActionStart,
    PostV1DesktopIdComputerActionDragMouseActionEnd,
    PostV1DesktopIdComputerActionGetCursorPositionAction,
    PostV1DesktopIdComputerActionGetCursorPositionActionType,
    PostV1DesktopIdComputerActionMoveMouseAction,
    PostV1DesktopIdComputerActionMoveMouseActionType,
    PostV1DesktopIdComputerActionPressKeysAction,
    PostV1DesktopIdComputerActionPressKeysActionType,
    PostV1DesktopIdComputerActionPressKeysActionKeyActionType as PressKeyActionType,
    PostV1DesktopIdComputerActionScreenshotAction,
    PostV1DesktopIdComputerActionScreenshotActionType,
    PostV1DesktopIdComputerActionScrollAction,
    PostV1DesktopIdComputerActionScrollActionType,
    PostV1DesktopIdComputerActionScrollActionDirection as ScrollDirection,
    PostV1DesktopIdComputerActionTypeTextAction,
    PostV1DesktopIdComputerActionTypeTextActionType,
    PostV1DesktopIdComputerActionWaitAction,
    PostV1DesktopIdComputerActionWaitActionType,
)

# Re-export the original Enum types under their aliased names for user convenience if they need to import them
# This makes `from cyberdesk.actions import ClickMouseButton` possible.

def click_mouse(
    x: Optional[int] = None,
    y: Optional[int] = None,
    button: Optional[ClickMouseButton] = None,
    num_of_clicks: Optional[int] = None,
    click_type: Optional[ClickMouseActionType] = None,
) -> PostV1DesktopIdComputerActionClickMouseAction:
    return PostV1DesktopIdComputerActionClickMouseAction(
        type_=PostV1DesktopIdComputerActionClickMouseActionType.CLICK_MOUSE,
        x=x if x is not None else UNSET,
        y=y if y is not None else UNSET,
        button=button if button is not None else UNSET,
        num_of_clicks=num_of_clicks if num_of_clicks is not None else UNSET,
        click_type=click_type if click_type is not None else UNSET
    )

def drag_mouse(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int
) -> PostV1DesktopIdComputerActionDragMouseAction:
    start_model = PostV1DesktopIdComputerActionDragMouseActionStart(x=start_x, y=start_y)
    end_model = PostV1DesktopIdComputerActionDragMouseActionEnd(x=end_x, y=end_y)
    return PostV1DesktopIdComputerActionDragMouseAction(
        type_=PostV1DesktopIdComputerActionDragMouseActionType.DRAG_MOUSE,
        start=start_model,
        end=end_model
    )

def get_cursor_position() -> PostV1DesktopIdComputerActionGetCursorPositionAction:
    return PostV1DesktopIdComputerActionGetCursorPositionAction(
        type_=PostV1DesktopIdComputerActionGetCursorPositionActionType.GET_CURSOR_POSITION
    )

def move_mouse(
    x: int,
    y: int
) -> PostV1DesktopIdComputerActionMoveMouseAction:
    return PostV1DesktopIdComputerActionMoveMouseAction(
        type_=PostV1DesktopIdComputerActionMoveMouseActionType.MOVE_MOUSE,
        x=x,
        y=y
    )

def press_keys(
    keys: Optional[Union[str, List[str]]] = None,
    key_action_type: Optional[PressKeyActionType] = None
) -> PostV1DesktopIdComputerActionPressKeysAction:
    return PostV1DesktopIdComputerActionPressKeysAction(
        type_=PostV1DesktopIdComputerActionPressKeysActionType.PRESS_KEYS,
        keys=keys if keys is not None else UNSET,
        key_action_type=key_action_type if key_action_type is not None else UNSET
    )

def screenshot() -> PostV1DesktopIdComputerActionScreenshotAction:
    return PostV1DesktopIdComputerActionScreenshotAction(
        type_=PostV1DesktopIdComputerActionScreenshotActionType.SCREENSHOT
    )

def scroll(
    direction: ScrollDirection,
    amount: int
) -> PostV1DesktopIdComputerActionScrollAction:
    return PostV1DesktopIdComputerActionScrollAction(
        type_=PostV1DesktopIdComputerActionScrollActionType.SCROLL,
        direction=direction,
        amount=amount
    )

def type_text(
    text: str
) -> PostV1DesktopIdComputerActionTypeTextAction:
    return PostV1DesktopIdComputerActionTypeTextAction(
        type_=PostV1DesktopIdComputerActionTypeTextActionType.TYPE,
        text=text
    )

def wait(
    ms: int
) -> PostV1DesktopIdComputerActionWaitAction:
    return PostV1DesktopIdComputerActionWaitAction(
        type_=PostV1DesktopIdComputerActionWaitActionType.WAIT,
        ms=ms
    ) 