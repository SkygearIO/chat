# pylama:ignore=W0401,W0611
from skygear import op
from skygear.container import SkygearContainer
from skygear.options import options
from .conversation import *
from .message import *


@op('chat-plugin-init')
def chat_plugin_init():
    container = SkygearContainer(api_key=options.masterkey)

    container.send_action('schema:create', {'record_types': {
        'user': {
            'fields': [
                {'name': 'name', 'type': 'string'}
            ]
        }
    }})

    container.send_action('schema:create', {'record_types': {
        'conversation': {
            'fields': [
                {'name': 'title', 'type': 'string'},
                {'name': 'admin_ids', 'type': 'json'},
                {'name': 'participant_ids', 'type': 'json'},
                {'name': 'is_direct_message', 'type': 'boolean'}
            ]
        }
    }})

    container.send_action('schema:create', {'record_types': {
        'message': {
            'fields': [
                {'name': 'attachment', 'type': 'asset'},
                {'name': 'body', 'type': 'string'},
                {'name': 'metadata', 'type': 'json'},
                {'name': 'conversation_id', 'type': 'ref(conversation)'}
            ]
        }
    }})

    container.send_action('schema:create', {'record_types': {
        'user_conversation': {
            'fields': [
                {'name': 'user', 'type': 'ref(user)'},
                {'name': 'conversation', 'type': 'ref(conversation)'},
                {'name': 'unread_count', 'type': 'number'},
                {'name': 'last_read_message', 'type': 'ref(message)'}
            ]
        }
    }})
