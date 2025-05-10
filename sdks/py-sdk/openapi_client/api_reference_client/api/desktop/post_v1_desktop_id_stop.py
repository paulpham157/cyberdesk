from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_v1_desktop_id_stop_response_200 import PostV1DesktopIdStopResponse200
from ...models.post_v1_desktop_id_stop_response_400 import PostV1DesktopIdStopResponse400
from ...models.post_v1_desktop_id_stop_response_401 import PostV1DesktopIdStopResponse401
from ...models.post_v1_desktop_id_stop_response_403 import PostV1DesktopIdStopResponse403
from ...models.post_v1_desktop_id_stop_response_404 import PostV1DesktopIdStopResponse404
from ...models.post_v1_desktop_id_stop_response_409 import PostV1DesktopIdStopResponse409
from ...models.post_v1_desktop_id_stop_response_429 import PostV1DesktopIdStopResponse429
from ...models.post_v1_desktop_id_stop_response_500 import PostV1DesktopIdStopResponse500
from ...models.post_v1_desktop_id_stop_response_502 import PostV1DesktopIdStopResponse502
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    x_api_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/v1/desktop/{id}/stop",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        PostV1DesktopIdStopResponse200,
        PostV1DesktopIdStopResponse400,
        PostV1DesktopIdStopResponse401,
        PostV1DesktopIdStopResponse403,
        PostV1DesktopIdStopResponse404,
        PostV1DesktopIdStopResponse409,
        PostV1DesktopIdStopResponse429,
        PostV1DesktopIdStopResponse500,
        PostV1DesktopIdStopResponse502,
    ]
]:
    if response.status_code == 200:
        response_200 = PostV1DesktopIdStopResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = PostV1DesktopIdStopResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = PostV1DesktopIdStopResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 403:
        response_403 = PostV1DesktopIdStopResponse403.from_dict(response.json())

        return response_403
    if response.status_code == 404:
        response_404 = PostV1DesktopIdStopResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 409:
        response_409 = PostV1DesktopIdStopResponse409.from_dict(response.json())

        return response_409
    if response.status_code == 429:
        response_429 = PostV1DesktopIdStopResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = PostV1DesktopIdStopResponse500.from_dict(response.json())

        return response_500
    if response.status_code == 502:
        response_502 = PostV1DesktopIdStopResponse502.from_dict(response.json())

        return response_502
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        PostV1DesktopIdStopResponse200,
        PostV1DesktopIdStopResponse400,
        PostV1DesktopIdStopResponse401,
        PostV1DesktopIdStopResponse403,
        PostV1DesktopIdStopResponse404,
        PostV1DesktopIdStopResponse409,
        PostV1DesktopIdStopResponse429,
        PostV1DesktopIdStopResponse500,
        PostV1DesktopIdStopResponse502,
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
    x_api_key: str,
) -> Response[
    Union[
        PostV1DesktopIdStopResponse200,
        PostV1DesktopIdStopResponse400,
        PostV1DesktopIdStopResponse401,
        PostV1DesktopIdStopResponse403,
        PostV1DesktopIdStopResponse404,
        PostV1DesktopIdStopResponse409,
        PostV1DesktopIdStopResponse429,
        PostV1DesktopIdStopResponse500,
        PostV1DesktopIdStopResponse502,
    ]
]:
    """Stop a running desktop instance

     Stops a running desktop instance and cleans up resources

    Args:
        id (str): Desktop instance ID to stop Example: desktop_12345.
        x_api_key (str): API key for authentication Example: api_12345.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PostV1DesktopIdStopResponse200, PostV1DesktopIdStopResponse400, PostV1DesktopIdStopResponse401, PostV1DesktopIdStopResponse403, PostV1DesktopIdStopResponse404, PostV1DesktopIdStopResponse409, PostV1DesktopIdStopResponse429, PostV1DesktopIdStopResponse500, PostV1DesktopIdStopResponse502]]
    """

    kwargs = _get_kwargs(
        id=id,
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
    x_api_key: str,
) -> Optional[
    Union[
        PostV1DesktopIdStopResponse200,
        PostV1DesktopIdStopResponse400,
        PostV1DesktopIdStopResponse401,
        PostV1DesktopIdStopResponse403,
        PostV1DesktopIdStopResponse404,
        PostV1DesktopIdStopResponse409,
        PostV1DesktopIdStopResponse429,
        PostV1DesktopIdStopResponse500,
        PostV1DesktopIdStopResponse502,
    ]
]:
    """Stop a running desktop instance

     Stops a running desktop instance and cleans up resources

    Args:
        id (str): Desktop instance ID to stop Example: desktop_12345.
        x_api_key (str): API key for authentication Example: api_12345.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PostV1DesktopIdStopResponse200, PostV1DesktopIdStopResponse400, PostV1DesktopIdStopResponse401, PostV1DesktopIdStopResponse403, PostV1DesktopIdStopResponse404, PostV1DesktopIdStopResponse409, PostV1DesktopIdStopResponse429, PostV1DesktopIdStopResponse500, PostV1DesktopIdStopResponse502]
    """

    return sync_detailed(
        id=id,
        client=client,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_key: str,
) -> Response[
    Union[
        PostV1DesktopIdStopResponse200,
        PostV1DesktopIdStopResponse400,
        PostV1DesktopIdStopResponse401,
        PostV1DesktopIdStopResponse403,
        PostV1DesktopIdStopResponse404,
        PostV1DesktopIdStopResponse409,
        PostV1DesktopIdStopResponse429,
        PostV1DesktopIdStopResponse500,
        PostV1DesktopIdStopResponse502,
    ]
]:
    """Stop a running desktop instance

     Stops a running desktop instance and cleans up resources

    Args:
        id (str): Desktop instance ID to stop Example: desktop_12345.
        x_api_key (str): API key for authentication Example: api_12345.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PostV1DesktopIdStopResponse200, PostV1DesktopIdStopResponse400, PostV1DesktopIdStopResponse401, PostV1DesktopIdStopResponse403, PostV1DesktopIdStopResponse404, PostV1DesktopIdStopResponse409, PostV1DesktopIdStopResponse429, PostV1DesktopIdStopResponse500, PostV1DesktopIdStopResponse502]]
    """

    kwargs = _get_kwargs(
        id=id,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_key: str,
) -> Optional[
    Union[
        PostV1DesktopIdStopResponse200,
        PostV1DesktopIdStopResponse400,
        PostV1DesktopIdStopResponse401,
        PostV1DesktopIdStopResponse403,
        PostV1DesktopIdStopResponse404,
        PostV1DesktopIdStopResponse409,
        PostV1DesktopIdStopResponse429,
        PostV1DesktopIdStopResponse500,
        PostV1DesktopIdStopResponse502,
    ]
]:
    """Stop a running desktop instance

     Stops a running desktop instance and cleans up resources

    Args:
        id (str): Desktop instance ID to stop Example: desktop_12345.
        x_api_key (str): API key for authentication Example: api_12345.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PostV1DesktopIdStopResponse200, PostV1DesktopIdStopResponse400, PostV1DesktopIdStopResponse401, PostV1DesktopIdStopResponse403, PostV1DesktopIdStopResponse404, PostV1DesktopIdStopResponse409, PostV1DesktopIdStopResponse429, PostV1DesktopIdStopResponse500, PostV1DesktopIdStopResponse502]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            x_api_key=x_api_key,
        )
    ).parsed
