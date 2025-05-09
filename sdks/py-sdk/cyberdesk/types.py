from openapi_client.api_reference_client.models import (
    PostV1DesktopBody,
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
from typing import Union

# Named parameter types for SDK methods
GetDesktopParams = str  # Desktop ID
LaunchDesktopParams = PostV1DesktopBody
TerminateDesktopParams = str  # Desktop ID
ExecuteBashActionParams = str  # Command string

# Strongly-typed union for all computer action models
ComputerActionModel = Union[
    PostV1DesktopIdComputerActionClickMouseAction,
    PostV1DesktopIdComputerActionDragMouseAction,
    PostV1DesktopIdComputerActionGetCursorPositionAction,
    PostV1DesktopIdComputerActionMoveMouseAction,
    PostV1DesktopIdComputerActionPressKeysAction,
    PostV1DesktopIdComputerActionScreenshotAction,
    PostV1DesktopIdComputerActionScrollAction,
    PostV1DesktopIdComputerActionTypeTextAction,
    PostV1DesktopIdComputerActionWaitAction,
]

# Re-export action models for ergonomic imports
__all__ = [
    "GetDesktopParams",
    "LaunchDesktopParams",
    "TerminateDesktopParams",
    "ExecuteBashActionParams",
    "ComputerActionModel",
    "PostV1DesktopIdComputerActionClickMouseAction",
    "PostV1DesktopIdComputerActionDragMouseAction",
    "PostV1DesktopIdComputerActionGetCursorPositionAction",
    "PostV1DesktopIdComputerActionMoveMouseAction",
    "PostV1DesktopIdComputerActionPressKeysAction",
    "PostV1DesktopIdComputerActionScreenshotAction",
    "PostV1DesktopIdComputerActionScrollAction",
    "PostV1DesktopIdComputerActionTypeTextAction",
    "PostV1DesktopIdComputerActionWaitAction",
] 