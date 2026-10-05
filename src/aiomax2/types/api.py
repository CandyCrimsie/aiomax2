from __future__ import annotations

from pydantic import Field

from .attachments import PhotoAttachmentPayload, VideoThumbnail
from .base import MAXObject
from .callback import Callback
from .message import CommentMessage, Message, NewMessageBody
from .user import BotCommand, ChatAdmin, ChatMember


class SimpleQueryResult(MAXObject):
    success: bool
    message: str | None = None


class SendMessageResult(MAXObject):
    message: Message


class SendCommentResult(MAXObject):
    message: CommentMessage


class MessageList(MAXObject):
    messages: list[Message]


class CommentMessageList(MAXObject):
    messages: list[CommentMessage]


class BotCommandsInfo(MAXObject):
    commands: list[BotCommand] | None = Field(default=None, max_length=32)


class GetPinnedMessageResult(MAXObject):
    message: Message | None = None


class ChatMembersList(MAXObject):
    members: list[ChatMember]
    marker: int | None = None


class ChatAdminsList(MAXObject):
    admins: list[ChatAdmin]


class FailedUserDetails(MAXObject):
    error_code: str
    user_ids: list[int]


class ModifyMembersResult(SimpleQueryResult):
    failed_user_ids: list[int] | None = None
    failed_user_details: list[FailedUserDetails] | None = None


class Subscription(MAXObject):
    url: str
    time: int
    update_types: list[str] | None = None


class GetSubscriptionsResult(MAXObject):
    subscriptions: list[Subscription]


class UploadEndpoint(MAXObject):
    url: str
    token: str | None = None


class VideoUrls(MAXObject):
    mp4_1080: str | None = None
    mp4_720: str | None = None
    mp4_480: str | None = None
    mp4_360: str | None = None
    mp4_240: str | None = None
    mp4_144: str | None = None
    hls: str | None = None


class VideoAttachmentDetails(MAXObject):
    token: str
    urls: VideoUrls | None = None
    thumbnail: PhotoAttachmentPayload | VideoThumbnail | None = None
    width: int
    height: int
    duration: int


class CallbackAnswer(MAXObject):
    message: NewMessageBody | None = None
    notification: str | None = None


class CallbackEnvelope(MAXObject):
    callback: Callback
