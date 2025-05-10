from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PostV1DesktopIdComputerActionDragMouseActionStart")


@_attrs_define
class PostV1DesktopIdComputerActionDragMouseActionStart:
    """Starting coordinates for the drag operation

    Example:
        {'x': 100, 'y': 100}

    Attributes:
        x (int): X coordinate on the screen Example: 500.
        y (int): Y coordinate on the screen Example: 300.
    """

    x: int
    y: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        x = self.x

        y = self.y

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "x": x,
                "y": y,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        x = d.pop("x")

        y = d.pop("y")

        post_v1_desktop_id_computer_action_drag_mouse_action_start = cls(
            x=x,
            y=y,
        )

        post_v1_desktop_id_computer_action_drag_mouse_action_start.additional_properties = d
        return post_v1_desktop_id_computer_action_drag_mouse_action_start

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
