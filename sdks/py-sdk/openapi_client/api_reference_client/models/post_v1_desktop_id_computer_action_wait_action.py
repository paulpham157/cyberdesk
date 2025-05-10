from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_v1_desktop_id_computer_action_wait_action_type import PostV1DesktopIdComputerActionWaitActionType

T = TypeVar("T", bound="PostV1DesktopIdComputerActionWaitAction")


@_attrs_define
class PostV1DesktopIdComputerActionWaitAction:
    """
    Attributes:
        type_ (PostV1DesktopIdComputerActionWaitActionType): Wait for the specified number of milliseconds Example:
            wait.
        ms (int): Time to wait in milliseconds Example: 1000.
    """

    type_: PostV1DesktopIdComputerActionWaitActionType
    ms: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        ms = self.ms

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "ms": ms,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = PostV1DesktopIdComputerActionWaitActionType(d.pop("type"))

        ms = d.pop("ms")

        post_v1_desktop_id_computer_action_wait_action = cls(
            type_=type_,
            ms=ms,
        )

        post_v1_desktop_id_computer_action_wait_action.additional_properties = d
        return post_v1_desktop_id_computer_action_wait_action

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
