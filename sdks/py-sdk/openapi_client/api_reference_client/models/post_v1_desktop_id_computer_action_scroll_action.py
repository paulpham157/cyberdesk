from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_v1_desktop_id_computer_action_scroll_action_direction import (
    PostV1DesktopIdComputerActionScrollActionDirection,
)
from ..models.post_v1_desktop_id_computer_action_scroll_action_type import PostV1DesktopIdComputerActionScrollActionType

T = TypeVar("T", bound="PostV1DesktopIdComputerActionScrollAction")


@_attrs_define
class PostV1DesktopIdComputerActionScrollAction:
    """
    Attributes:
        type_ (PostV1DesktopIdComputerActionScrollActionType): Scroll the mouse wheel in the specified direction
            Example: scroll.
        direction (PostV1DesktopIdComputerActionScrollActionDirection): Direction to scroll Example: down.
        amount (int): Amount to scroll in pixels Example: 100.
    """

    type_: PostV1DesktopIdComputerActionScrollActionType
    direction: PostV1DesktopIdComputerActionScrollActionDirection
    amount: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        direction = self.direction.value

        amount = self.amount

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "direction": direction,
                "amount": amount,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = PostV1DesktopIdComputerActionScrollActionType(d.pop("type"))

        direction = PostV1DesktopIdComputerActionScrollActionDirection(d.pop("direction"))

        amount = d.pop("amount")

        post_v1_desktop_id_computer_action_scroll_action = cls(
            type_=type_,
            direction=direction,
            amount=amount,
        )

        post_v1_desktop_id_computer_action_scroll_action.additional_properties = d
        return post_v1_desktop_id_computer_action_scroll_action

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
