from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_v1_desktop_body import PostV1DesktopBody
from ...models.post_v1_desktop_response_200 import PostV1DesktopResponse200
from ...models.post_v1_desktop_response_400 import PostV1DesktopResponse400
from ...models.post_v1_desktop_response_401 import PostV1DesktopResponse401
from ...models.post_v1_desktop_response_403 import PostV1DesktopResponse403
from ...models.post_v1_desktop_response_404 import PostV1DesktopResponse404
from ...models.post_v1_desktop_response_409 import PostV1DesktopResponse409
from ...models.post_v1_desktop_response_429 import PostV1DesktopResponse429
from ...models.post_v1_desktop_response_500 import PostV1DesktopResponse500
from ...models.post_v1_desktop_response_502 import PostV1DesktopResponse502
from ...types import Response


def _get_kwargs(
    *,
    body: PostV1DesktopBody,
    x_api_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/desktop",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        PostV1DesktopResponse200,
        PostV1DesktopResponse400,
        PostV1DesktopResponse401,
        PostV1DesktopResponse403,
        PostV1DesktopResponse404,
        PostV1DesktopResponse409,
        PostV1DesktopResponse429,
        PostV1DesktopResponse500,
        PostV1DesktopResponse502,
    ]
]:
    if response.status_code == 200:
        response_200 = PostV1DesktopResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = PostV1DesktopResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = PostV1DesktopResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 403:
        response_403 = PostV1DesktopResponse403.from_dict(response.json())

        return response_403
    if response.status_code == 404:
        response_404 = PostV1DesktopResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 409:
        response_409 = PostV1DesktopResponse409.from_dict(response.json())

        return response_409
    if response.status_code == 429:
        response_429 = PostV1DesktopResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = PostV1DesktopResponse500.from_dict(response.json())

        return response_500
    if response.status_code == 502:
        response_502 = PostV1DesktopResponse502.from_dict(response.json())

        return response_502
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        PostV1DesktopResponse200,
        PostV1DesktopResponse400,
        PostV1DesktopResponse401,
        PostV1DesktopResponse403,
        PostV1DesktopResponse404,
        PostV1DesktopResponse409,
        PostV1DesktopResponse429,
        PostV1DesktopResponse500,
        PostV1DesktopResponse502,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostV1DesktopBody,
    x_api_key: str,
) -> Response[
    Union[
        PostV1DesktopResponse200,
        PostV1DesktopResponse400,
        PostV1DesktopResponse401,
        PostV1DesktopResponse403,
        PostV1DesktopResponse404,
        PostV1DesktopResponse409,
        PostV1DesktopResponse429,
        PostV1DesktopResponse500,
        PostV1DesktopResponse502,
    ]
]:
    """Create a new virtual desktop instance

     Creates a new virtual desktop instance and returns its ID and stream URL

    Args:
        x_api_key (str): API key for authentication Example: api_12345.
        body (PostV1DesktopBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PostV1DesktopResponse200, PostV1DesktopResponse400, PostV1DesktopResponse401, PostV1DesktopResponse403, PostV1DesktopResponse404, PostV1DesktopResponse409, PostV1DesktopResponse429, PostV1DesktopResponse500, PostV1DesktopResponse502]]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostV1DesktopBody,
    x_api_key: str,
) -> Optional[
    Union[
        PostV1DesktopResponse200,
        PostV1DesktopResponse400,
        PostV1DesktopResponse401,
        PostV1DesktopResponse403,
        PostV1DesktopResponse404,
        PostV1DesktopResponse409,
        PostV1DesktopResponse429,
        PostV1DesktopResponse500,
        PostV1DesktopResponse502,
    ]
]:
    """Create a new virtual desktop instance

     Creates a new virtual desktop instance and returns its ID and stream URL

    Args:
        x_api_key (str): API key for authentication Example: api_12345.
        body (PostV1DesktopBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PostV1DesktopResponse200, PostV1DesktopResponse400, PostV1DesktopResponse401, PostV1DesktopResponse403, PostV1DesktopResponse404, PostV1DesktopResponse409, PostV1DesktopResponse429, PostV1DesktopResponse500, PostV1DesktopResponse502]
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostV1DesktopBody,
    x_api_key: str,
) -> Response[
    Union[
        PostV1DesktopResponse200,
        PostV1DesktopResponse400,
        PostV1DesktopResponse401,
        PostV1DesktopResponse403,
        PostV1DesktopResponse404,
        PostV1DesktopResponse409,
        PostV1DesktopResponse429,
        PostV1DesktopResponse500,
        PostV1DesktopResponse502,
    ]
]:
    """Create a new virtual desktop instance

     Creates a new virtual desktop instance and returns its ID and stream URL

    Args:
        x_api_key (str): API key for authentication Example: api_12345.
        body (PostV1DesktopBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[PostV1DesktopResponse200, PostV1DesktopResponse400, PostV1DesktopResponse401, PostV1DesktopResponse403, PostV1DesktopResponse404, PostV1DesktopResponse409, PostV1DesktopResponse429, PostV1DesktopResponse500, PostV1DesktopResponse502]]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostV1DesktopBody,
    x_api_key: str,
) -> Optional[
    Union[
        PostV1DesktopResponse200,
        PostV1DesktopResponse400,
        PostV1DesktopResponse401,
        PostV1DesktopResponse403,
        PostV1DesktopResponse404,
        PostV1DesktopResponse409,
        PostV1DesktopResponse429,
        PostV1DesktopResponse500,
        PostV1DesktopResponse502,
    ]
]:
    """Create a new virtual desktop instance

     Creates a new virtual desktop instance and returns its ID and stream URL

    Args:
        x_api_key (str): API key for authentication Example: api_12345.
        body (PostV1DesktopBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[PostV1DesktopResponse200, PostV1DesktopResponse400, PostV1DesktopResponse401, PostV1DesktopResponse403, PostV1DesktopResponse404, PostV1DesktopResponse409, PostV1DesktopResponse429, PostV1DesktopResponse500, PostV1DesktopResponse502]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_key=x_api_key,
        )
    ).parsed
