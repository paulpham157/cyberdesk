import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.get_v1_desktop_id_response_200_status import GetV1DesktopIdResponse200Status

T = TypeVar("T", bound="GetV1DesktopIdResponse200")


@_attrs_define
class GetV1DesktopIdResponse200:
    """
    Attributes:
        id (UUID): Unique identifier for the desktop instance Example: a1b2c3d4-e5f6-7890-1234-567890abcdef.
        status (GetV1DesktopIdResponse200Status): Current status of the desktop instance Example: running.
        stream_url (Union[None, str]): URL for the desktop stream (null if the desktop is not running) Example:
            https://cyberdesk.com/vnc/a1b2c3d4-e5f6-7890-1234-567890abcdef.
        created_at (datetime.datetime): Timestamp when the instance was created Example: 2023-10-27T10:00:00Z.
        timeout_at (datetime.datetime): Timestamp when the instance will automatically time out Example:
            2023-10-28T10:00:00Z.
    """

    id: UUID
    status: GetV1DesktopIdResponse200Status
    stream_url: Union[None, str]
    created_at: datetime.datetime
    timeout_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        status = self.status.value

        stream_url: Union[None, str]
        stream_url = self.stream_url

        created_at = self.created_at.isoformat()

        timeout_at = self.timeout_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "status": status,
                "stream_url": stream_url,
                "created_at": created_at,
                "timeout_at": timeout_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        status = GetV1DesktopIdResponse200Status(d.pop("status"))

        def _parse_stream_url(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        stream_url = _parse_stream_url(d.pop("stream_url"))

        created_at = isoparse(d.pop("created_at"))

        timeout_at = isoparse(d.pop("timeout_at"))

        get_v1_desktop_id_response_200 = cls(
            id=id,
            status=status,
            stream_url=stream_url,
            created_at=created_at,
            timeout_at=timeout_at,
        )

        get_v1_desktop_id_response_200.additional_properties = d
        return get_v1_desktop_id_response_200

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
