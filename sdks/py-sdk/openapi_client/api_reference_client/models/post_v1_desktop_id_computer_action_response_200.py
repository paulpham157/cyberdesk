from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostV1DesktopIdComputerActionResponse200")


@_attrs_define
class PostV1DesktopIdComputerActionResponse200:
    """
    Attributes:
        output (Union[Unset, str]): Raw string output from the executed command (if any) Example: X=500 Y=300.
        error (Union[Unset, str]): Error message if the operation failed (also indicated by non-2xx HTTP status)
            Example: Command failed with code 1: xdotool: command not found.
        base64_image (Union[Unset, str]): Base64 encoded JPEG image data (only returned for screenshot actions) Example:
            /9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQ....
    """

    output: Union[Unset, str] = UNSET
    error: Union[Unset, str] = UNSET
    base64_image: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        output = self.output

        error = self.error

        base64_image = self.base64_image

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if output is not UNSET:
            field_dict["output"] = output
        if error is not UNSET:
            field_dict["error"] = error
        if base64_image is not UNSET:
            field_dict["base64_image"] = base64_image

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        output = d.pop("output", UNSET)

        error = d.pop("error", UNSET)

        base64_image = d.pop("base64_image", UNSET)

        post_v1_desktop_id_computer_action_response_200 = cls(
            output=output,
            error=error,
            base64_image=base64_image,
        )

        post_v1_desktop_id_computer_action_response_200.additional_properties = d
        return post_v1_desktop_id_computer_action_response_200

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
