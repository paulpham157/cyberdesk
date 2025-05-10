from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_v1_desktop_id_computer_action_type_text_action_type import (
    PostV1DesktopIdComputerActionTypeTextActionType,
)

T = TypeVar("T", bound="PostV1DesktopIdComputerActionTypeTextAction")


@_attrs_define
class PostV1DesktopIdComputerActionTypeTextAction:
    """
    Attributes:
        type_ (PostV1DesktopIdComputerActionTypeTextActionType): Type text at the current cursor position Example: type.
        text (str): Text to type Example: Hello, World!.
    """

    type_: PostV1DesktopIdComputerActionTypeTextActionType
    text: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        text = self.text

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "text": text,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = PostV1DesktopIdComputerActionTypeTextActionType(d.pop("type"))

        text = d.pop("text")

        post_v1_desktop_id_computer_action_type_text_action = cls(
            type_=type_,
            text=text,
        )

        post_v1_desktop_id_computer_action_type_text_action.additional_properties = d
        return post_v1_desktop_id_computer_action_type_text_action

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
