from enum import StrEnum


class ChatType(StrEnum):
    DIALOG = "dialog"
    CHAT = "chat"
    CHANNEL = "channel"


class ChatStatus(StrEnum):
    ACTIVE = "active"
    REMOVED = "removed"
    LEFT = "left"
    CLOSED = "closed"
    SUSPENDED = "suspended"


class ChatAdminPermission(StrEnum):
    READ_ALL_MESSAGES = "read_all_messages"
    ADD_REMOVE_MEMBERS = "add_remove_members"
    ADD_ADMINS = "add_admins"
    CHANGE_CHAT_INFO = "change_chat_info"
    PIN_MESSAGE = "pin_message"
    EDIT_LINK = "edit_link"
    WRITE = "write"
    EDIT = "edit"
    DELETE = "delete"
    CAN_CALL = "can_call"
    VIEW_STATS = "view_stats"


class TextFormat(StrEnum):
    MARKDOWN = "markdown"
    HTML = "html"


class MessageLinkType(StrEnum):
    FORWARD = "forward"
    REPLY = "reply"


class UploadType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"


class SenderAction(StrEnum):
    TYPING_ON = "typing_on"
    SENDING_PHOTO = "sending_photo"
    SENDING_VIDEO = "sending_video"
    SENDING_AUDIO = "sending_audio"
    SENDING_FILE = "sending_file"
    MARK_SEEN = "mark_seen"


class UpdateType(StrEnum):
    MESSAGE_CREATED = "message_created"
    MESSAGE_CALLBACK = "message_callback"
    MESSAGE_EDITED = "message_edited"
    MESSAGE_REMOVED = "message_removed"
    COMMENT_CREATED = "comment_created"
    COMMENT_EDITED = "comment_edited"
    COMMENT_REMOVED = "comment_removed"
    BOT_ADDED = "bot_added"
    BOT_REMOVED = "bot_removed"
    USER_ADDED = "user_added"
    USER_REMOVED = "user_removed"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    DIALOG_CLEARED = "dialog_cleared"
    DIALOG_REMOVED = "dialog_removed"
    DIALOG_MUTED = "dialog_muted"
    DIALOG_UNMUTED = "dialog_unmuted"
    CHAT_TITLE_CHANGED = "chat_title_changed"
    BOT_ADMIN_PERMISSIONS_CHANGED = "bot_admin_permissions_changed"


class AttachmentType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    STICKER = "sticker"
    CONTACT = "contact"
    INLINE_KEYBOARD = "inline_keyboard"
    SHARE = "share"
    LOCATION = "location"


class ButtonType(StrEnum):
    CALLBACK = "callback"
    LINK = "link"
    REQUEST_GEO_LOCATION = "request_geo_location"
    REQUEST_CONTACT = "request_contact"
    MESSAGE = "message"
    OPEN_APP = "open_app"
    CLIPBOARD = "clipboard"
