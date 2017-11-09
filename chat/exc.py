from skygear.error import (InvalidArgument, NotSupported, PermissionDenied,
                           SkygearException)


"""
Exception used in Skygear Chat Plugin
"""


class SkygearChatException(SkygearException):
    pass


class ConversationAlreadyExistsException(SkygearException):
    def __init__(self, conversation_id):
        super().__init__(
            "Conversation with the participants already exists",
            InvalidArgument,
            {'conversation_id': conversation_id}
        )


class NotInConversationException(SkygearChatException):
    def __init__(self):
        super().__init__(
            "user is not in the conversation, permission denied",
            PermissionDenied
        )


class NotAdminConversationException(SkygearChatException):
    def __init__(self):
        super().__init__(
            "user is not an admin, permission denied",
            PermissionDenied
        )


class MessageNotFoundException(SkygearChatException):
    def __init__(self):
        super().__init__(
            "message not found",
            InvalidArgument
        )


class ConversationNotFoundException(SkygearChatException):
    def __init__(self):
        super().__init__(
            "conversation not found",
            InvalidArgument
        )


class AlreadyDeletedException(SkygearChatException):
    def __init__(self):
        super().__init__(
            "message is already deleted",
            InvalidArgument
        )


class InvalidGetMessagesConditionArgumentException(SkygearChatException):
    def __init__(self):
        super().__init__(
            "cannot use both message_id and time to filter",
            InvalidArgument
        )


class NotSupportedException(SkygearChatException):
    def __init__(self, message=None):
        message = message or "This operation is not supported."
        super().__init__(
            message,
            NotSupported
        )


class InvalidArgumentException(SkygearChatException):
    def __init__(self, message=None, arguments=None):
        message = message or "This operation is not supported."
        arguments = arguments if isinstance(arguments, list) else []
        super().__init__(
            message,
            InvalidArgument,
            {
                'arguments': arguments,
            }
        )
