from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_v1_desktop_id_computer_action_click_mouse_action import (
    PostV1DesktopIdComputerActionClickMouseAction,
)
from ...models.post_v1_desktop_id_computer_action_drag_mouse_action import PostV1DesktopIdComputerActionDragMouseAction
from ...models.post_v1_desktop_id_computer_action_get_cursor_position_action import (
    PostV1DesktopIdComputerActionGetCursorPositionAction,
)
from ...models.post_v1_desktop_id_computer_action_move_mouse_action import PostV1DesktopIdComputerActionMoveMouseAction
from ...models.post_v1_desktop_id_computer_action_press_keys_action import PostV1DesktopIdComputerActionPressKeysAction
from ...models.post_v1_desktop_id_computer_action_response_200 import PostV1DesktopIdComputerActionResponse200
from ...models.post_v1_desktop_id_computer_action_response_400 import PostV1DesktopIdComputerActionResponse400
from ...models.post_v1_desktop_id_computer_action_response_401 import PostV1DesktopIdComputerActionResponse401
from ...models.post_v1_desktop_id_computer_action_response_403 import PostV1DesktopIdComputerActionResponse403
from ...models.post_v1_desktop_id_computer_action_response_404 import PostV1DesktopIdComputerActionResponse404
from ...models.post_v1_desktop_id_computer_action_response_409 import PostV1DesktopIdComputerActionResponse409
from ...models.post_v1_desktop_id_computer_action_response_429 import PostV1DesktopIdComputerActionResponse429
from ...models.post_v1_desktop_id_computer_action_response_500 import PostV1DesktopIdComputerActionResponse500
from ...models.post_v1_desktop_id_computer_action_response_502 import PostV1DesktopIdComputerActionResponse502
from ...models.post_v1_desktop_id_computer_action_screenshot_action import PostV1DesktopIdComputerActionScreenshotAction
from ...models.post_v1_desktop_id_computer_action_scroll_action import PostV1DesktopIdComputerActionScrollAction
from ...models.post_v1_desktop_id_computer_action_type_text_action import PostV1DesktopIdComputerActionTypeTextAction
from ...models.post_v1_desktop_id_computer_action_wait_action import PostV1DesktopIdComputerActionWaitAction
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    body: Union[
        "PostV1DesktopIdComputerActionClickMouseAction",
        "PostV1DesktopIdComputerActionDragMouseAction",
        "PostV1DesktopIdComputerActionGetCursorPositionAction",
        "PostV1DesktopIdComputerActionMoveMouseAction",
        "PostV1DesktopIdComputerActionPressKeysAction",
        "PostV1DesktopIdComputerActionScreenshotAction",
        "PostV1DesktopIdComputerActionScrollAction",
        "PostV1DesktopIdComputerActionTypeTextAction",
        "PostV1DesktopIdComputerActionWaitAction",
    ],
    x_api_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/v1/desktop/{id}/computer-action",
    }

    _body: dict[str, Any]
    if isinstance(body, PostV1DesktopIdComputerActionClickMouseAction):
        _body = body.to_dict()
    elif isinstance(body, PostV1DesktopIdComputerActionScrollAction):
        _body = body.to_dict()
    elif isinstance(body, PostV1DesktopIdComputerActionMoveMouseAction):
        _body = body.to_dict()
    elif isinstance(body, PostV1DesktopIdComputerActionDragMouseAction):
        _body = body.to_dict()
    elif isinstance(body, PostV1DesktopIdComputerActionTypeTextAction):
        _body = body.to_dict()
    elif isinstance(body, PostV1DesktopIdComputerActionPressKeysAction):
        _body = body.to_dict()
    elif isinstance(body, PostV1DesktopIdComputerActionWaitAction):
        _body = body.to_dict()
    elif isinstance(body, PostV1DesktopIdComputerActionScreenshotAction):
        _body = body.to_dict()
    else:
        _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        PostV1DesktopIdComputerActionResponse200,
        PostV1DesktopIdComputerActionResponse400,
        PostV1DesktopIdComputerActionResponse401,
        PostV1DesktopIdComputerActionResponse403,
        PostV1DesktopIdComputerActionResponse404,
        PostV1DesktopIdComputerActionResponse409,
        PostV1DesktopIdComputerActionResponse429,
        PostV1DesktopIdComputerActionResponse500,
        PostV1DesktopIdComputerActionResponse502,
    ]
]:
    if response.status_code == 200:
        response_200 = PostV1DesktopIdComputerActionResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = PostV1DesktopIdComputerActionResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = PostV1DesktopIdComputerActionResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 403:
        response_403 = PostV1DesktopIdComputerActionResponse403.from_dict(response.json())

        return response_403
    if response.status_code == 404:
        response_404 = PostV1DesktopIdComputerActionResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 409:
        response_409 = PostV1DesktopIdComputerActionResponse409.from_dict(response.json())

        return response_409
    if response.status_code == 429:
        response_429 = PostV1DesktopIdComputerActionResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = PostV1DesktopIdComputerActionResponse500.from_dict(response.json())

        return response_500
    if response.status_code == 502:
        response_502 = PostV1DesktopIdComputerActionResponse502.from_dict(response.json())

        return response_502
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        PostV1DesktopIdComputerActionResponse200,
        PostV1DesktopIdComputerActionResponse400,
        PostV1DesktopIdComputerActionResponse401,
        PostV1DesktopIdComputerActionResponse403,
        PostV1DesktopIdComputerActionResponse404,
        PostV1DesktopIdComputerActionResponse409,
        PostV1DesktopIdComputerActionResponse429,
        PostV1DesktopIdComputerActionResponse500,
        PostV1DesktopIdComputerActionResponse502,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "PostV1DesktopIdComputerActionClickMouseAction",
        "PostV1DesktopIdComputerActionDragMouseAction",
        "PostV1DesktopIdComputerActionGetCursorPositionAction",
        "PostV1DesktopIdComputerActionMoveMouseAction",
        "PostV1DesktopIdComputerActionPressKeysAction",
        "PostV1DesktopIdComputerActionScreenshotAction",
        "PostV1DesktopIdComputerActionScrollAction",
        "PostV1DesktopIdComputerActionTypeTextAction",
        "PostV1DesktopIdComputerActionWaitAction",
    ],
    x_api_key: str,
) -> Response[
    Union[
        PostV1DesktopIdComputerActionResponse200,
        PostV1DesktopIdComputerActionResponse400,
        PostV1DesktopIdComputerActionResponse401,
        PostV1DesktopIdComputerActionResponse403,
        PostV1DesktopIdComputerActionResponse404,
        PostV1DesktopIdComputerActionResponse409,
        PostV1DesktopIdComputerActionResponse429,
        PostV1DesktopIdComputerActionResponse500,
        PostV1DesktopIdComputerActionResponse502,
    ]
]:
    """Perform an action on the desktop

     Executes a computer action such as mouse clicks, keyboard input, or screenshots on the desktop

    Args:
        id (str): Desktop instance ID to perform the action on Example: desktop_12345.
        x_api_key (str): API key for authentication Example: api_12345.
        body (Union['PostV1DesktopIdComputerActionClickMouseAction',
            'PostV1DesktopIdComputerActionDragMouseAction',
            'PostV1DesktopIdComputerActionGetCursorPositionAction',
            'PostV1DesktopIdComputerActionMoveMouseAction',
            'PostV1DesktopIdComputerActionPressKeysAction',
            'PostV1DesktopIdComputerActionScreenshotAction',
            'PostV1DesktopIdComputerActionScrollAction',
            'PostV1DesktopIdComputerActionTypeTextAction',
            'PostV1DesktopIdComputerActionWaitAction']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PostV1DesktopIdComputerActionResponse200, PostV1DesktopIdComputerActionResponse400, PostV1DesktopIdComputerActionResponse401, PostV1DesktopIdComputerActionResponse403, PostV1DesktopIdComputerActionResponse404, PostV1DesktopIdComputerActionResponse409, PostV1DesktopIdComputerActionResponse429, PostV1DesktopIdComputerActionResponse500, PostV1DesktopIdComputerActionResponse502]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "PostV1DesktopIdComputerActionClickMouseAction",
        "PostV1DesktopIdComputerActionDragMouseAction",
        "PostV1DesktopIdComputerActionGetCursorPositionAction",
        "PostV1DesktopIdComputerActionMoveMouseAction",
        "PostV1DesktopIdComputerActionPressKeysAction",
        "PostV1DesktopIdComputerActionScreenshotAction",
        "PostV1DesktopIdComputerActionScrollAction",
        "PostV1DesktopIdComputerActionTypeTextAction",
        "PostV1DesktopIdComputerActionWaitAction",
    ],
    x_api_key: str,
) -> Optional[
    Union[
        PostV1DesktopIdComputerActionResponse200,
        PostV1DesktopIdComputerActionResponse400,
        PostV1DesktopIdComputerActionResponse401,
        PostV1DesktopIdComputerActionResponse403,
        PostV1DesktopIdComputerActionResponse404,
        PostV1DesktopIdComputerActionResponse409,
        PostV1DesktopIdComputerActionResponse429,
        PostV1DesktopIdComputerActionResponse500,
        PostV1DesktopIdComputerActionResponse502,
    ]
]:
    """Perform an action on the desktop

     Executes a computer action such as mouse clicks, keyboard input, or screenshots on the desktop

    Args:
        id (str): Desktop instance ID to perform the action on Example: desktop_12345.
        x_api_key (str): API key for authentication Example: api_12345.
        body (Union['PostV1DesktopIdComputerActionClickMouseAction',
            'PostV1DesktopIdComputerActionDragMouseAction',
            'PostV1DesktopIdComputerActionGetCursorPositionAction',
            'PostV1DesktopIdComputerActionMoveMouseAction',
            'PostV1DesktopIdComputerActionPressKeysAction',
            'PostV1DesktopIdComputerActionScreenshotAction',
            'PostV1DesktopIdComputerActionScrollAction',
            'PostV1DesktopIdComputerActionTypeTextAction',
            'PostV1DesktopIdComputerActionWaitAction']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PostV1DesktopIdComputerActionResponse200, PostV1DesktopIdComputerActionResponse400, PostV1DesktopIdComputerActionResponse401, PostV1DesktopIdComputerActionResponse403, PostV1DesktopIdComputerActionResponse404, PostV1DesktopIdComputerActionResponse409, PostV1DesktopIdComputerActionResponse429, PostV1DesktopIdComputerActionResponse500, PostV1DesktopIdComputerActionResponse502]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "PostV1DesktopIdComputerActionClickMouseAction",
        "PostV1DesktopIdComputerActionDragMouseAction",
        "PostV1DesktopIdComputerActionGetCursorPositionAction",
        "PostV1DesktopIdComputerActionMoveMouseAction",
        "PostV1DesktopIdComputerActionPressKeysAction",
        "PostV1DesktopIdComputerActionScreenshotAction",
        "PostV1DesktopIdComputerActionScrollAction",
        "PostV1DesktopIdComputerActionTypeTextAction",
        "PostV1DesktopIdComputerActionWaitAction",
    ],
    x_api_key: str,
) -> Response[
    Union[
        PostV1DesktopIdComputerActionResponse200,
        PostV1DesktopIdComputerActionResponse400,
        PostV1DesktopIdComputerActionResponse401,
        PostV1DesktopIdComputerActionResponse403,
        PostV1DesktopIdComputerActionResponse404,
        PostV1DesktopIdComputerActionResponse409,
        PostV1DesktopIdComputerActionResponse429,
        PostV1DesktopIdComputerActionResponse500,
        PostV1DesktopIdComputerActionResponse502,
    ]
]:
    """Perform an action on the desktop

     Executes a computer action such as mouse clicks, keyboard input, or screenshots on the desktop

    Args:
        id (str): Desktop instance ID to perform the action on Example: desktop_12345.
        x_api_key (str): API key for authentication Example: api_12345.
        body (Union['PostV1DesktopIdComputerActionClickMouseAction',
            'PostV1DesktopIdComputerActionDragMouseAction',
            'PostV1DesktopIdComputerActionGetCursorPositionAction',
            'PostV1DesktopIdComputerActionMoveMouseAction',
            'PostV1DesktopIdComputerActionPressKeysAction',
            'PostV1DesktopIdComputerActionScreenshotAction',
            'PostV1DesktopIdComputerActionScrollAction',
            'PostV1DesktopIdComputerActionTypeTextAction',
            'PostV1DesktopIdComputerActionWaitAction']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PostV1DesktopIdComputerActionResponse200, PostV1DesktopIdComputerActionResponse400, PostV1DesktopIdComputerActionResponse401, PostV1DesktopIdComputerActionResponse403, PostV1DesktopIdComputerActionResponse404, PostV1DesktopIdComputerActionResponse409, PostV1DesktopIdComputerActionResponse429, PostV1DesktopIdComputerActionResponse500, PostV1DesktopIdComputerActionResponse502]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "PostV1DesktopIdComputerActionClickMouseAction",
        "PostV1DesktopIdComputerActionDragMouseAction",
        "PostV1DesktopIdComputerActionGetCursorPositionAction",
        "PostV1DesktopIdComputerActionMoveMouseAction",
        "PostV1DesktopIdComputerActionPressKeysAction",
        "PostV1DesktopIdComputerActionScreenshotAction",
        "PostV1DesktopIdComputerActionScrollAction",
        "PostV1DesktopIdComputerActionTypeTextAction",
        "PostV1DesktopIdComputerActionWaitAction",
    ],
    x_api_key: str,
) -> Optional[
    Union[
        PostV1DesktopIdComputerActionResponse200,
        PostV1DesktopIdComputerActionResponse400,
        PostV1DesktopIdComputerActionResponse401,
        PostV1DesktopIdComputerActionResponse403,
        PostV1DesktopIdComputerActionResponse404,
        PostV1DesktopIdComputerActionResponse409,
        PostV1DesktopIdComputerActionResponse429,
        PostV1DesktopIdComputerActionResponse500,
        PostV1DesktopIdComputerActionResponse502,
    ]
]:
    """Perform an action on the desktop

     Executes a computer action such as mouse clicks, keyboard input, or screenshots on the desktop

    Args:
        id (str): Desktop instance ID to perform the action on Example: desktop_12345.
        x_api_key (str): API key for authentication Example: api_12345.
        body (Union['PostV1DesktopIdComputerActionClickMouseAction',
            'PostV1DesktopIdComputerActionDragMouseAction',
            'PostV1DesktopIdComputerActionGetCursorPositionAction',
            'PostV1DesktopIdComputerActionMoveMouseAction',
            'PostV1DesktopIdComputerActionPressKeysAction',
            'PostV1DesktopIdComputerActionScreenshotAction',
            'PostV1DesktopIdComputerActionScrollAction',
            'PostV1DesktopIdComputerActionTypeTextAction',
            'PostV1DesktopIdComputerActionWaitAction']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PostV1DesktopIdComputerActionResponse200, PostV1DesktopIdComputerActionResponse400, PostV1DesktopIdComputerActionResponse401, PostV1DesktopIdComputerActionResponse403, PostV1DesktopIdComputerActionResponse404, PostV1DesktopIdComputerActionResponse409, PostV1DesktopIdComputerActionResponse429, PostV1DesktopIdComputerActionResponse500, PostV1DesktopIdComputerActionResponse502]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
            x_api_key=x_api_key,
        )
    ).parsed
