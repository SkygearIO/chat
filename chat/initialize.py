import skygear
from skygear.container import SkygearContainer
from skygear.options import options as skyoptions


def register_initialization_event_handlers(settings):
    def _base_message_fields():
        return [{
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
                    'name': 'conversation',
                    'type': 'ref(conversation)'
                },
                {
                    'name': 'message_status',
                    'type': 'string'
                },
                {
                    'name': 'seq',
                    'type': 'sequence'
                }]

    def _message_schema():
        fields = _base_message_fields() + [{
                                            'name': 'deleted',
                                            'type': 'boolean'
                                           }]
        return {'fields': fields}

    def _message_history_schema():
        fields = _base_message_fields() + [{
                                            'name': 'parent',
                                            'type': 'ref(message)'
                                           }]
        return {'fields': fields}

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
                    'message': _message_schema(),
                    'message_history': _message_history_schema()
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
                                'name': 'user',
                                'type': 'ref(user)'
                            },
                            {
                                'name': 'message',
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
