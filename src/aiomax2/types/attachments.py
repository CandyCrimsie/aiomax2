from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .base import MAXObject
from .user import User


class PhotoAttachmentPayload(MAXObject):
    photo_id: int | None = None
    token: str | None = None
    url: str | None = None


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
    url: str | None = None


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
    text: str


class CallbackButton(BaseButton):
    type: Literal["callback"] = "callback"
    payload: str


class LinkButton(BaseButton):
    type: Literal["link"] = "link"
    url: str


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
    payload: str | None = None
    contact_id: int | None = None


class ClipboardButton(BaseButton):
    type: Literal["clipboard"] = "clipboard"
    payload: str


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
    url: str | None = None
    token: str | None = None
    photos: dict[str, PhotoToken] | None = None

    @model_validator(mode="after")
    def validate_source(self) -> PhotoAttachmentRequestPayload:
        if not any((self.url, self.token, self.photos)):
            raise ValueError("one of url, token or photos must be provided")
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
