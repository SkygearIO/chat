from skygear.error import (InvalidArgument, NotSupported, PermissionDenied,
                           SkygearException)


"""
Exception used in Skygear Chat Plugin
"""


class SkygearChatException(SkygearException):
    pass


class NotInConversationException(SkygearChatException):
    def __init__(self):
        super().__init__(
            "user not in conversation, permission denied",
            PermissionDenied
        )


class MessageNotFoundException(SkygearChatException):
    def __init__(self):
        super().__init__(
            "message not found",
            InvalidArgument
        )


class AlreadyDeletedException(SkygearChatException):
    def __init__(self):
        super().__init__(
            "message is already deleted",
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
