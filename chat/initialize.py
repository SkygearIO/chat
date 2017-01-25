import skygear
from skygear.container import SkygearContainer
from skygear.options import options as skyoptions


def register_initialization_event_handlers(settings):
    @skygear.event("before-plugins-ready")
    def chat_plugin_init(config):
        container = SkygearContainer(api_key=skyoptions.masterkey)
        container.send_action(
            'schema:create',
            {
                'record_types': {
                    'user': {
                        'fields': [
                            {'name': 'name', 'type': 'string'}
                        ]
                    },
                    'conversation': {
                        'fields': [
                            {
                                'name': 'title',
                                'type': 'string'
                            },
                            {
                                'name': 'admin_ids',
                                'type': 'json'
                            },
                            {
                                'name': 'participant_ids',
                                'type': 'json'
                            },
                            {
                                'name': 'participant_count',
                                'type': 'number'
                            },
                            {
                                'name': 'metadata',
                                'type': 'json'
                            },
                            {
                                'name': 'distinct_by_participants',
                                'type': 'boolean'
                            }
                        ]
                    }
                }
            },
            plugin_request=True
        )
        container.send_action(
            'schema:create',
            {
                'record_types': {
                    'message': {
                        'fields': [
                            {
                                'name': 'attachment',
                                'type': 'asset'
                            },
                            {
                                'name': 'body',
                                'type': 'string'
                            },
                            {
                                'name': 'metadata',
                                'type': 'json'
                            },
                            {
                                'name': 'conversation_id',
                                'type': 'ref(conversation)'
                            },
                            {
                                'name': 'conversation_status',
                                'type': 'string'
                            }
                        ]
                    }
                }
            },
            plugin_request=True
        )
        container.send_action(
            'schema:create',
            {
                'record_types': {
                    'user_conversation': {
                        'fields': [
                            {
                                'name': 'user',
                                'type': 'ref(user)'
                            },
                            {
                                'name': 'conversation',
                                'type': 'ref(conversation)'
                            },
                            {
                                'name': 'unread_count',
                                'type': 'number'
                            },
                            {
                                'name': 'last_read_message',
                                'type': 'ref(message)'
                            }
                        ]
                    },
                    'receipt': {
                        'fields': [
                            {
                                'name': 'user_id',
                                'type': 'ref(user)'
                            },
                            {
                                'name': 'message_id',
                                'type': 'ref(message)'
                            },
                            {
                                'name': 'read_at',
                                'type': 'datetime'
                            },
                            {
                                'name': 'delivered_at',
                                'type': 'datetime'
                            }
                        ]
                    },
                    'conversation': {
                        'fields': [
                            {
                                'name': 'last_message',
                                'type': 'ref(message)'
                            }
                        ]
                    }
                }
            },
            plugin_request=True
        )
