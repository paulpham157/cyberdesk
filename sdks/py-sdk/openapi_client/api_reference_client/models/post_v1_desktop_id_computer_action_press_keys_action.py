from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_v1_desktop_id_computer_action_press_keys_action_key_action_type import (
    PostV1DesktopIdComputerActionPressKeysActionKeyActionType,
)
from ..models.post_v1_desktop_id_computer_action_press_keys_action_type import (
    PostV1DesktopIdComputerActionPressKeysActionType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="PostV1DesktopIdComputerActionPressKeysAction")


@_attrs_define
class PostV1DesktopIdComputerActionPressKeysAction:
    """
    Attributes:
        type_ (PostV1DesktopIdComputerActionPressKeysActionType): Press, hold down, or release one or more keyboard
            keys. Defaults to a single press and release. Example: press_keys.
        keys (Union[list[str], str]):
        key_action_type (Union[Unset, PostV1DesktopIdComputerActionPressKeysActionKeyActionType]): Type of key action
            (optional, defaults to 'press' which is a down and up action) Example: press.
    """

    type_: PostV1DesktopIdComputerActionPressKeysActionType
    keys: Union[list[str], str]
    key_action_type: Union[Unset, PostV1DesktopIdComputerActionPressKeysActionKeyActionType] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        keys: Union[list[str], str]
        if isinstance(self.keys, list):
            keys = self.keys

        else:
            keys = self.keys

        key_action_type: Union[Unset, str] = UNSET
        if not isinstance(self.key_action_type, Unset):
            key_action_type = self.key_action_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "keys": keys,
            }
        )
        if key_action_type is not UNSET:
            field_dict["key_action_type"] = key_action_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = PostV1DesktopIdComputerActionPressKeysActionType(d.pop("type"))

        def _parse_keys(data: object) -> Union[list[str], str]:
            try:
                if not isinstance(data, list):
                    raise TypeError()
                keys_type_1 = cast(list[str], data)

                return keys_type_1
            except:  # noqa: E722
                pass
            return cast(Union[list[str], str], data)

        keys = _parse_keys(d.pop("keys"))

        _key_action_type = d.pop("key_action_type", UNSET)
        key_action_type: Union[Unset, PostV1DesktopIdComputerActionPressKeysActionKeyActionType]
        if isinstance(_key_action_type, Unset):
            key_action_type = UNSET
        else:
            key_action_type = PostV1DesktopIdComputerActionPressKeysActionKeyActionType(_key_action_type)

        post_v1_desktop_id_computer_action_press_keys_action = cls(
            type_=type_,
            keys=keys,
            key_action_type=key_action_type,
        )

        post_v1_desktop_id_computer_action_press_keys_action.additional_properties = d
        return post_v1_desktop_id_computer_action_press_keys_action

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
