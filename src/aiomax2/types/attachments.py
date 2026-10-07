from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .base import MAXObject
from .user import User


class PhotoAttachmentPayload(MAXObject):
    photo_id: int
    token: str
    url: str


class MediaAttachmentPayload(MAXObject):
    token: str


class FileAttachmentPayload(MAXObject):
    token: str


class ContactAttachmentPayload(MAXObject):
    vcf_info: str | None = None
    hash: str | None = None
    max_info: User | None = None


class StickerAttachmentPayload(MAXObject):
    code: str


class ShareAttachmentPayload(MAXObject):
    url: str | None = None
    token: str | None = None


class VideoThumbnail(MAXObject):
    url: str


class BaseAttachment(MAXObject):
    type: str


class PhotoAttachment(BaseAttachment):
    type: Literal["image"] = "image"
    payload: PhotoAttachmentPayload


class VideoAttachment(BaseAttachment):
    type: Literal["video"] = "video"
    payload: MediaAttachmentPayload
    thumbnail: VideoThumbnail | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None


class AudioAttachment(BaseAttachment):
    type: Literal["audio"] = "audio"
    payload: MediaAttachmentPayload
    transcription: str | None = None


class FileAttachment(BaseAttachment):
    type: Literal["file"] = "file"
    payload: FileAttachmentPayload
    filename: str
    size: int


class ContactAttachment(BaseAttachment):
    type: Literal["contact"] = "contact"
    payload: ContactAttachmentPayload


class StickerAttachment(BaseAttachment):
    type: Literal["sticker"] = "sticker"
    payload: StickerAttachmentPayload
    width: int
    height: int


class ShareAttachment(BaseAttachment):
    type: Literal["share"] = "share"
    payload: ShareAttachmentPayload
    title: str | None = None
    description: str | None = None
    image_url: str | None = None


class LocationAttachment(BaseAttachment):
    type: Literal["location"] = "location"
    latitude: float
    longitude: float


class BaseButton(MAXObject):
    type: str
    text: Annotated[str, Field(min_length=1, max_length=128)]


class CallbackButton(BaseButton):
    type: Literal["callback"] = "callback"
    payload: Annotated[str, Field(max_length=1024)]


class LinkButton(BaseButton):
    type: Literal["link"] = "link"
    url: Annotated[str, Field(max_length=2048)]


class RequestGeoLocationButton(BaseButton):
    type: Literal["request_geo_location"] = "request_geo_location"
    quick: bool | None = None


class RequestContactButton(BaseButton):
    type: Literal["request_contact"] = "request_contact"


class MessageButton(BaseButton):
    type: Literal["message"] = "message"


class OpenAppButton(BaseButton):
    type: Literal["open_app"] = "open_app"
    web_app: str
    payload: (
        Annotated[str, Field(max_length=512, pattern=r"^[A-Za-z0-9_-]*$")] | None
    ) = None
    contact_id: int | None = None


class ClipboardButton(BaseButton):
    type: Literal["clipboard"] = "clipboard"
    payload: Annotated[str, Field(max_length=1024)]


Button = Annotated[
    CallbackButton
    | LinkButton
    | RequestGeoLocationButton
    | RequestContactButton
    | MessageButton
    | OpenAppButton
    | ClipboardButton,
    Field(discriminator="type"),
]


class Keyboard(MAXObject):
    buttons: list[list[Button]]

    @model_validator(mode="after")
    def validate_layout(self) -> Keyboard:
        if not self.buttons:
            raise ValueError("keyboard must contain at least one row")
        if len(self.buttons) > 30:
            raise ValueError("keyboard cannot contain more than 30 rows")

        restricted_types = {
            "link",
            "open_app",
            "request_geo_location",
            "request_contact",
        }
        total = 0
        for row in self.buttons:
            if not row:
                raise ValueError("keyboard rows cannot be empty")
            if len(row) > 7:
                raise ValueError("keyboard rows cannot contain more than 7 buttons")
            if len(row) > 3 and any(button.type in restricted_types for button in row):
                raise ValueError(
                    "rows containing link, open_app, request_geo_location or "
                    "request_contact buttons cannot contain more than 3 buttons"
                )
            total += len(row)

        if total > 210:
            raise ValueError("keyboard cannot contain more than 210 buttons")
        return self


class InlineKeyboardAttachment(BaseAttachment):
    type: Literal["inline_keyboard"] = "inline_keyboard"
    payload: Keyboard


Attachment = Annotated[
    PhotoAttachment
    | VideoAttachment
    | AudioAttachment
    | FileAttachment
    | ContactAttachment
    | StickerAttachment
    | ShareAttachment
    | LocationAttachment
    | InlineKeyboardAttachment,
    Field(discriminator="type"),
]


class UploadedInfo(MAXObject):
    token: str


class PhotoToken(MAXObject):
    token: str


class PhotoAttachmentRequestPayload(MAXObject):
    url: Annotated[str, Field(min_length=1)] | None = None
    token: str | None = None
    photos: dict[str, PhotoToken] | None = None

    @model_validator(mode="after")
    def validate_source(self) -> PhotoAttachmentRequestPayload:
        source_count = sum(
            source is not None for source in (self.url, self.token, self.photos)
        )
        if source_count != 1:
            raise ValueError("exactly one of url, token or photos must be provided")
        return self


class ContactAttachmentRequestPayload(MAXObject):
    name: str | None = None
    contact_id: int | None = None
    vcf_info: str | None = None
    vcf_phone: str | None = None


class BaseAttachmentRequest(MAXObject):
    type: str


class PhotoAttachmentRequest(BaseAttachmentRequest):
    type: Literal["image"] = "image"
    payload: PhotoAttachmentRequestPayload


class VideoAttachmentRequest(BaseAttachmentRequest):
    type: Literal["video"] = "video"
    payload: UploadedInfo


class AudioAttachmentRequest(BaseAttachmentRequest):
    type: Literal["audio"] = "audio"
    payload: UploadedInfo


class FileAttachmentRequest(BaseAttachmentRequest):
    type: Literal["file"] = "file"
    payload: UploadedInfo


class ContactAttachmentRequest(BaseAttachmentRequest):
    type: Literal["contact"] = "contact"
    payload: ContactAttachmentRequestPayload


class StickerAttachmentRequest(BaseAttachmentRequest):
    type: Literal["sticker"] = "sticker"
    payload: StickerAttachmentPayload


class InlineKeyboardAttachmentRequest(BaseAttachmentRequest):
    type: Literal["inline_keyboard"] = "inline_keyboard"
    payload: Keyboard


class LocationAttachmentRequest(BaseAttachmentRequest):
    type: Literal["location"] = "location"
    latitude: float
    longitude: float


class ShareAttachmentRequest(BaseAttachmentRequest):
    type: Literal["share"] = "share"
    payload: ShareAttachmentPayload


AttachmentRequest = Annotated[
    PhotoAttachmentRequest
    | VideoAttachmentRequest
    | AudioAttachmentRequest
    | FileAttachmentRequest
    | ContactAttachmentRequest
    | StickerAttachmentRequest
    | InlineKeyboardAttachmentRequest
    | LocationAttachmentRequest
    | ShareAttachmentRequest,
    Field(discriminator="type"),
]


class MarkupElement(MAXObject):
    type: str
    from_: int = Field(alias="from", serialization_alias="from")
    length: int
    url: str | None = None
    user_link: str | None = None
    user_id: int | None = None
