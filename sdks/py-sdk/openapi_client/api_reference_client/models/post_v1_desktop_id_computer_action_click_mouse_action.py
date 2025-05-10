from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_v1_desktop_id_computer_action_click_mouse_action_button import (
    PostV1DesktopIdComputerActionClickMouseActionButton,
)
from ..models.post_v1_desktop_id_computer_action_click_mouse_action_click_type import (
    PostV1DesktopIdComputerActionClickMouseActionClickType,
)
from ..models.post_v1_desktop_id_computer_action_click_mouse_action_type import (
    PostV1DesktopIdComputerActionClickMouseActionType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="PostV1DesktopIdComputerActionClickMouseAction")


@_attrs_define
class PostV1DesktopIdComputerActionClickMouseAction:
    """
    Attributes:
        type_ (PostV1DesktopIdComputerActionClickMouseActionType): Perform a mouse action: click, press (down), or
            release (up). Defaults to a single left click at the current position. Example: click_mouse.
        x (Union[Unset, int]): X coordinate for the action (optional, uses current position if omitted) Example: 500.
        y (Union[Unset, int]): Y coordinate for the action (optional, uses current position if omitted) Example: 300.
        button (Union[Unset, PostV1DesktopIdComputerActionClickMouseActionButton]): Mouse button to use (optional,
            defaults to 'left') Example: left.
        num_of_clicks (Union[Unset, int]): Number of clicks to perform (optional, defaults to 1, only applicable for
            'click' type) Example: 1.
        click_type (Union[Unset, PostV1DesktopIdComputerActionClickMouseActionClickType]): Type of mouse action
            (optional, defaults to 'click') Example: click.
    """

    type_: PostV1DesktopIdComputerActionClickMouseActionType
    x: Union[Unset, int] = UNSET
    y: Union[Unset, int] = UNSET
    button: Union[Unset, PostV1DesktopIdComputerActionClickMouseActionButton] = UNSET
    num_of_clicks: Union[Unset, int] = UNSET
    click_type: Union[Unset, PostV1DesktopIdComputerActionClickMouseActionClickType] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        x = self.x

        y = self.y

        button: Union[Unset, str] = UNSET
        if not isinstance(self.button, Unset):
            button = self.button.value

        num_of_clicks = self.num_of_clicks

        click_type: Union[Unset, str] = UNSET
        if not isinstance(self.click_type, Unset):
            click_type = self.click_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if x is not UNSET:
            field_dict["x"] = x
        if y is not UNSET:
            field_dict["y"] = y
        if button is not UNSET:
            field_dict["button"] = button
        if num_of_clicks is not UNSET:
            field_dict["num_of_clicks"] = num_of_clicks
        if click_type is not UNSET:
            field_dict["click_type"] = click_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = PostV1DesktopIdComputerActionClickMouseActionType(d.pop("type"))

        x = d.pop("x", UNSET)

        y = d.pop("y", UNSET)

        _button = d.pop("button", UNSET)
        button: Union[Unset, PostV1DesktopIdComputerActionClickMouseActionButton]
        if isinstance(_button, Unset):
            button = UNSET
        else:
            button = PostV1DesktopIdComputerActionClickMouseActionButton(_button)

        num_of_clicks = d.pop("num_of_clicks", UNSET)

        _click_type = d.pop("click_type", UNSET)
        click_type: Union[Unset, PostV1DesktopIdComputerActionClickMouseActionClickType]
        if isinstance(_click_type, Unset):
            click_type = UNSET
        else:
            click_type = PostV1DesktopIdComputerActionClickMouseActionClickType(_click_type)

        post_v1_desktop_id_computer_action_click_mouse_action = cls(
            type_=type_,
            x=x,
            y=y,
            button=button,
            num_of_clicks=num_of_clicks,
            click_type=click_type,
        )

        post_v1_desktop_id_computer_action_click_mouse_action.additional_properties = d
        return post_v1_desktop_id_computer_action_click_mouse_action

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
