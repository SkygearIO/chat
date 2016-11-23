from skygear.error import PermissionDenied, SkygearException


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
