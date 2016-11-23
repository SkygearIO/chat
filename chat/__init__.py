from .conversation import register_conversation_hooks
from .initialize import register_initialization_event_handlers
from .message import register_message_hooks, register_message_lambdas
from .typing import register_typing_lambda
from .user_conversation import (register_user_conversation_hooks,
                                register_user_conversation_lambdas)


def includeme(settings):
    register_initialization_event_handlers(settings)
    register_conversation_hooks(settings)
    register_message_hooks(settings)
    register_message_lambdas(settings)
    register_user_conversation_hooks(settings)
    register_user_conversation_lambdas(settings)
    register_typing_lambda(settings)
