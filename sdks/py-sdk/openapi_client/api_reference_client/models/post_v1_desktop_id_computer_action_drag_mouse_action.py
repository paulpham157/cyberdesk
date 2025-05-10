from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_v1_desktop_id_computer_action_drag_mouse_action_type import (
    PostV1DesktopIdComputerActionDragMouseActionType,
)

if TYPE_CHECKING:
    from ..models.post_v1_desktop_id_computer_action_drag_mouse_action_end import (
        PostV1DesktopIdComputerActionDragMouseActionEnd,
    )
    from ..models.post_v1_desktop_id_computer_action_drag_mouse_action_start import (
        PostV1DesktopIdComputerActionDragMouseActionStart,
    )


T = TypeVar("T", bound="PostV1DesktopIdComputerActionDragMouseAction")


@_attrs_define
class PostV1DesktopIdComputerActionDragMouseAction:
    """
    Attributes:
        type_ (PostV1DesktopIdComputerActionDragMouseActionType): Drag the mouse from start to end coordinates Example:
            drag_mouse.
        start (PostV1DesktopIdComputerActionDragMouseActionStart): Starting coordinates for the drag operation Example:
            {'x': 100, 'y': 100}.
        end (PostV1DesktopIdComputerActionDragMouseActionEnd): Ending coordinates for the drag operation Example: {'x':
            300, 'y': 300}.
    """

    type_: PostV1DesktopIdComputerActionDragMouseActionType
    start: "PostV1DesktopIdComputerActionDragMouseActionStart"
    end: "PostV1DesktopIdComputerActionDragMouseActionEnd"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        start = self.start.to_dict()

        end = self.end.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "start": start,
                "end": end,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_v1_desktop_id_computer_action_drag_mouse_action_end import (
            PostV1DesktopIdComputerActionDragMouseActionEnd,
        )
        from ..models.post_v1_desktop_id_computer_action_drag_mouse_action_start import (
            PostV1DesktopIdComputerActionDragMouseActionStart,
        )

        d = dict(src_dict)
        type_ = PostV1DesktopIdComputerActionDragMouseActionType(d.pop("type"))

        start = PostV1DesktopIdComputerActionDragMouseActionStart.from_dict(d.pop("start"))

        end = PostV1DesktopIdComputerActionDragMouseActionEnd.from_dict(d.pop("end"))

        post_v1_desktop_id_computer_action_drag_mouse_action = cls(
            type_=type_,
            start=start,
            end=end,
        )

        post_v1_desktop_id_computer_action_drag_mouse_action.additional_properties = d
        return post_v1_desktop_id_computer_action_drag_mouse_action

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
