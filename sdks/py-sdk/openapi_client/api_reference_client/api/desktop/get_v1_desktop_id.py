from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v1_desktop_id_response_200 import GetV1DesktopIdResponse200
from ...models.get_v1_desktop_id_response_400 import GetV1DesktopIdResponse400
from ...models.get_v1_desktop_id_response_401 import GetV1DesktopIdResponse401
from ...models.get_v1_desktop_id_response_403 import GetV1DesktopIdResponse403
from ...models.get_v1_desktop_id_response_404 import GetV1DesktopIdResponse404
from ...models.get_v1_desktop_id_response_409 import GetV1DesktopIdResponse409
from ...models.get_v1_desktop_id_response_429 import GetV1DesktopIdResponse429
from ...models.get_v1_desktop_id_response_500 import GetV1DesktopIdResponse500
from ...models.get_v1_desktop_id_response_502 import GetV1DesktopIdResponse502
from ...types import Response


def _get_kwargs(
    id: UUID,
    *,
    x_api_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/desktop/{id}",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetV1DesktopIdResponse200,
        GetV1DesktopIdResponse400,
        GetV1DesktopIdResponse401,
        GetV1DesktopIdResponse403,
        GetV1DesktopIdResponse404,
        GetV1DesktopIdResponse409,
        GetV1DesktopIdResponse429,
        GetV1DesktopIdResponse500,
        GetV1DesktopIdResponse502,
    ]
]:
    if response.status_code == 200:
        response_200 = GetV1DesktopIdResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = GetV1DesktopIdResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = GetV1DesktopIdResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 403:
        response_403 = GetV1DesktopIdResponse403.from_dict(response.json())

        return response_403
    if response.status_code == 404:
        response_404 = GetV1DesktopIdResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 409:
        response_409 = GetV1DesktopIdResponse409.from_dict(response.json())

        return response_409
    if response.status_code == 429:
        response_429 = GetV1DesktopIdResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetV1DesktopIdResponse500.from_dict(response.json())

        return response_500
    if response.status_code == 502:
        response_502 = GetV1DesktopIdResponse502.from_dict(response.json())

        return response_502
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        GetV1DesktopIdResponse200,
        GetV1DesktopIdResponse400,
        GetV1DesktopIdResponse401,
        GetV1DesktopIdResponse403,
        GetV1DesktopIdResponse404,
        GetV1DesktopIdResponse409,
        GetV1DesktopIdResponse429,
        GetV1DesktopIdResponse500,
        GetV1DesktopIdResponse502,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_key: str,
) -> Response[
    Union[
        GetV1DesktopIdResponse200,
        GetV1DesktopIdResponse400,
        GetV1DesktopIdResponse401,
        GetV1DesktopIdResponse403,
        GetV1DesktopIdResponse404,
        GetV1DesktopIdResponse409,
        GetV1DesktopIdResponse429,
        GetV1DesktopIdResponse500,
        GetV1DesktopIdResponse502,
    ]
]:
    """Get details of a specific desktop instance

     Returns the ID, status, creation timestamp, and timeout timestamp for a given desktop instance.

    Args:
        id (UUID): The UUID of the desktop instance to retrieve Example:
            a1b2c3d4-e5f6-7890-1234-567890abcdef.
        x_api_key (str): API key for authentication Example: api_12345.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetV1DesktopIdResponse200, GetV1DesktopIdResponse400, GetV1DesktopIdResponse401, GetV1DesktopIdResponse403, GetV1DesktopIdResponse404, GetV1DesktopIdResponse409, GetV1DesktopIdResponse429, GetV1DesktopIdResponse500, GetV1DesktopIdResponse502]]
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
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_key: str,
) -> Optional[
    Union[
        GetV1DesktopIdResponse200,
        GetV1DesktopIdResponse400,
        GetV1DesktopIdResponse401,
        GetV1DesktopIdResponse403,
        GetV1DesktopIdResponse404,
        GetV1DesktopIdResponse409,
        GetV1DesktopIdResponse429,
        GetV1DesktopIdResponse500,
        GetV1DesktopIdResponse502,
    ]
]:
    """Get details of a specific desktop instance

     Returns the ID, status, creation timestamp, and timeout timestamp for a given desktop instance.

    Args:
        id (UUID): The UUID of the desktop instance to retrieve Example:
            a1b2c3d4-e5f6-7890-1234-567890abcdef.
        x_api_key (str): API key for authentication Example: api_12345.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetV1DesktopIdResponse200, GetV1DesktopIdResponse400, GetV1DesktopIdResponse401, GetV1DesktopIdResponse403, GetV1DesktopIdResponse404, GetV1DesktopIdResponse409, GetV1DesktopIdResponse429, GetV1DesktopIdResponse500, GetV1DesktopIdResponse502]
    """

    return sync_detailed(
        id=id,
        client=client,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_key: str,
) -> Response[
    Union[
        GetV1DesktopIdResponse200,
        GetV1DesktopIdResponse400,
        GetV1DesktopIdResponse401,
        GetV1DesktopIdResponse403,
        GetV1DesktopIdResponse404,
        GetV1DesktopIdResponse409,
        GetV1DesktopIdResponse429,
        GetV1DesktopIdResponse500,
        GetV1DesktopIdResponse502,
    ]
]:
    """Get details of a specific desktop instance

     Returns the ID, status, creation timestamp, and timeout timestamp for a given desktop instance.

    Args:
        id (UUID): The UUID of the desktop instance to retrieve Example:
            a1b2c3d4-e5f6-7890-1234-567890abcdef.
        x_api_key (str): API key for authentication Example: api_12345.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetV1DesktopIdResponse200, GetV1DesktopIdResponse400, GetV1DesktopIdResponse401, GetV1DesktopIdResponse403, GetV1DesktopIdResponse404, GetV1DesktopIdResponse409, GetV1DesktopIdResponse429, GetV1DesktopIdResponse500, GetV1DesktopIdResponse502]]
    """

    kwargs = _get_kwargs(
        id=id,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_key: str,
) -> Optional[
    Union[
        GetV1DesktopIdResponse200,
        GetV1DesktopIdResponse400,
        GetV1DesktopIdResponse401,
        GetV1DesktopIdResponse403,
        GetV1DesktopIdResponse404,
        GetV1DesktopIdResponse409,
        GetV1DesktopIdResponse429,
        GetV1DesktopIdResponse500,
        GetV1DesktopIdResponse502,
    ]
]:
    """Get details of a specific desktop instance

     Returns the ID, status, creation timestamp, and timeout timestamp for a given desktop instance.

    Args:
        id (UUID): The UUID of the desktop instance to retrieve Example:
            a1b2c3d4-e5f6-7890-1234-567890abcdef.
        x_api_key (str): API key for authentication Example: api_12345.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetV1DesktopIdResponse200, GetV1DesktopIdResponse400, GetV1DesktopIdResponse401, GetV1DesktopIdResponse403, GetV1DesktopIdResponse404, GetV1DesktopIdResponse409, GetV1DesktopIdResponse429, GetV1DesktopIdResponse500, GetV1DesktopIdResponse502]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            x_api_key=x_api_key,
        )
    ).parsed
