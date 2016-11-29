from skygear.error import NotSupported, PermissionDenied, SkygearException


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


class NotSupportedException(SkygearChatException):
    def __init__(self, message=None):
        message = message or "This operation is not supported."
        super().__init__(
            message,
            NotSupported
        )
