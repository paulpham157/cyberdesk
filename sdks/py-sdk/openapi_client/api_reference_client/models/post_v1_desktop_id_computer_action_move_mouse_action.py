from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_v1_desktop_id_computer_action_move_mouse_action_type import (
    PostV1DesktopIdComputerActionMoveMouseActionType,
)

T = TypeVar("T", bound="PostV1DesktopIdComputerActionMoveMouseAction")


@_attrs_define
class PostV1DesktopIdComputerActionMoveMouseAction:
    """
    Attributes:
        type_ (PostV1DesktopIdComputerActionMoveMouseActionType): Move the mouse cursor to the specified coordinates
            Example: move_mouse.
        x (int): X coordinate to move to Example: 500.
        y (int): Y coordinate to move to Example: 300.
    """

    type_: PostV1DesktopIdComputerActionMoveMouseActionType
    x: int
    y: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        x = self.x

        y = self.y

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "x": x,
                "y": y,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = PostV1DesktopIdComputerActionMoveMouseActionType(d.pop("type"))

        x = d.pop("x")

        y = d.pop("y")

        post_v1_desktop_id_computer_action_move_mouse_action = cls(
            type_=type_,
            x=x,
            y=y,
        )

        post_v1_desktop_id_computer_action_move_mouse_action.additional_properties = d
        return post_v1_desktop_id_computer_action_move_mouse_action

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
